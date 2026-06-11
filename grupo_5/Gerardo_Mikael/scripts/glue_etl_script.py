import sys
from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F

# Glue and spark context setup
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# JDBC config
JDBC_URL = "jdbc:mysql://classicmodels-db.c4iczixrubp8.us-east-1.rds.amazonaws.com/classicmodels"
DB_USER = "admin"
DB_PASS = "SENHAFORTEDETESTE"

S3_TARGET_BUCKET = "s3://classicmodels-data-lake-gerardo-mikael-projetos"

print("Iniciando leitura das tabelas de origem do RDS...")

def read_rds_table(table_name):
    return spark.read.format("jdbc") \
        .option("url", JDBC_URL) \
        .option("dbtable", table_name) \
        .option("user", DB_USER) \
        .option("password", DB_PASS) \
        .option("driver", "com.mysql.cj.jdbc.Driver") \
        .load()

# Tabelas base
df_orders       = read_rds_table("orders")
df_orderdetails = read_rds_table("orderdetails")
df_customers    = read_rds_table("customers")
df_products     = read_rds_table("products")
df_employees    = read_rds_table("employees")
df_offices      = read_rds_table("offices")

print("Transformando dados para o Modelo Estrela...")

# DIM_CUSTOMERS
dim_customers = df_customers.select(
    F.col("customerNumber").alias("customer_id"),
    F.col("customerName").alias("customer_name"),
    F.concat_ws(" ", F.col("contactFirstName"), F.col("contactLastName")).alias("contact_name"),
    F.col("city"),
    F.col("country")
)

# DIM_PRODUCTS
dim_products = df_products.select(
    F.col("productCode").alias("product_id"),
    F.col("productName").alias("product_name"),
    F.col("productLine").alias("product_line"),
    F.col("productVendor").alias("product_vendor")
)

# DIM_DATES
dim_dates = (
    df_orders.select("orderDate").distinct()
    .withColumn("date_key", F.date_format("orderDate", "yyyyMMdd").cast("int"))
    .withColumn("full_date", F.col("orderDate"))
    .withColumn("year", F.year("orderDate"))
    .withColumn("quarter", F.quarter("orderDate"))
    .withColumn("month", F.month("orderDate"))
    .withColumn("day", F.dayofmonth("orderDate"))
)

# DIM_COUNTRIES (cliente + território comercial)
dim_countries = (
    df_customers
    .join(
        df_employees,
        df_customers.salesRepEmployeeNumber == df_employees.employeeNumber,
        "left"
    )
    .join(
        df_offices,
        df_employees.officeCode == df_offices.officeCode,
        "left"
    )
    .select(
        df_customers.country.alias("country"),
        df_offices.territory.alias("territory")
    )
    .distinct()
    .withColumn("country_key", F.monotonically_increasing_id())
)

# FACT TABLE BASE
fact_orders_raw = (
    df_orders
    .join(df_orderdetails, "orderNumber")
    .join(df_customers, "customerNumber")
)

fact_orders = (
    fact_orders_raw
    .join(
        dim_countries,
        fact_orders_raw["country"] == dim_countries["country"],
        "left"
    )
    .select(
        F.col("orderNumber").alias("order_id"),
        F.col("customerNumber").alias("customer_id"),
        F.col("productCode").alias("product_id"),
        F.date_format("orderDate", "yyyyMMdd").cast("int").alias("order_date_key"),
        F.col("country_key"),
        F.col("quantityOrdered").alias("quantity_ordered"),
        F.col("priceEach").alias("price_each"),
        (F.col("quantityOrdered") * F.col("priceEach")).alias("sales_amount")
    )
)

print("Iniciando escrita no S3...")

def write_to_parquet(df, name):
    path = f"{S3_TARGET_BUCKET}/{name}"
    print(f"Escrevendo {name} em {path}")
    df.write.mode("overwrite").parquet(path)

write_to_parquet(fact_orders, "fact_orders")
write_to_parquet(dim_customers, "dim_customers")
write_to_parquet(dim_products, "dim_products")
write_to_parquet(dim_dates, "dim_dates")
write_to_parquet(dim_countries, "dim_countries")

print("Pipeline finalizado com sucesso.")
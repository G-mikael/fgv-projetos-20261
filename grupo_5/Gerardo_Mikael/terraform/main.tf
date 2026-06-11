#Provider block
provider "aws" {
  profile = "default"
  region = "us-east-1"
}

# Instancia do S3 para o Data Lake

resource "aws_s3_bucket" "data_lake" {
  bucket = "classicmodels-data-lake-gerardo-mikael-projetos"
}

#Security Group de forma simplificada sem limitação de ip, para fins de teste. Em produção, é recomendado restringir o acesso apenas aos IPs necessários
#Mudar isso depois (talvez?) 

resource "aws_security_group" "mysql_sg" {
  name = "mysql-sg"

  ingress {
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Autoreferência para a conexão do glue (conexões na mesma VPC)
  ingress {
    description = "Permite que recursos com este mesmo SG conversem entre si"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    self        = true 
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Instância RDS MySQL
# Para o banco de dados do projeto

resource "aws_db_instance" "mysql" {
  identifier             = "classicmodels-db"
  allocated_storage      = 20
  engine                 = "mysql"
  engine_version         = "8.0"
  instance_class         = "db.t3.micro"

  username               = "admin"
  password               = var.db_password

  publicly_accessible    = true
  skip_final_snapshot    = true

  vpc_security_group_ids = [
    aws_security_group.mysql_sg.id
  ]
}

# Conexão do Glue com o RDS MySQL e criação do Glue Job para o processo de ETL.
# Capturar a role do aws academy lab para usar no Glue Job
data "aws_iam_role" "academy_lab_role" {
  name = "LabRole"
}

# conexão do Glue com o RDS MySQL
resource "aws_glue_connection" "rds_mysql_connection" {
  name = "glue-rds-mysql-conn"

  connection_properties = {
    # Monta a URL JDBC dinamicamente
    JDBC_CONNECTION_URL = "jdbc:mysql://${aws_db_instance.mysql.endpoint}/classicmodels"
    USERNAME            = "admin"
    PASSWORD            = var.db_password
  }

  physical_connection_requirements {
    # O Glue precisa rodar na mesma zona e subnet que o RDS para "enxergá-lo"
    availability_zone      = aws_db_instance.mysql.availability_zone
    security_group_id_list = [aws_security_group.mysql_sg.id]
    # Houve um problema de subnet_id do rds, devido ao aws academy lab criar os recursos em uma VPC padrão
    # Corrijido com a captura das subnets da VPC padrão da conta AWS, usando o data source aws_subnets 
    subnet_id              = data.aws_subnets.default.ids[0]
  }
}

# Glue job
resource "aws_glue_job" "etl_job" {
  name              = "classicmodels-etl-star-schema"
  role_arn          = data.aws_iam_role.academy_lab_role.arn
  glue_version      = "4.0" # Suporte a Python 3 e Spark de forma otimizada
  worker_type       = "G.1X"
  number_of_workers = 2

  command {
    name            = "glueetl"
    # Caminho no S3 onde o Glue vai buscar o script que vamos criar a seguir
    script_location = "s3://${aws_s3_bucket.data_lake.bucket}/scripts/glue_etl_script.py"
    python_version  = "3"
  }

  # Vincula a conexão de rede do RDS ao Job
  connections = [aws_glue_connection.rds_mysql_connection.name]

  default_arguments = {
    "--job-language"        = "python"
    "--job-bookmark-option" = "job-bookmark-disable" # Evita que o Glue pule dados já lidos em testes
    "--enable-metrics"      = "true"
  }
}

# Upload do script de transformação para o S3
resource "aws_s3_object" "upload_glue_script" {
  bucket = aws_s3_bucket.data_lake.bucket
  
  # Como ficará salvo no S3
  key    = "scripts/glue_etl_script.py" 
  source = "${path.module}/../scripts/glue_etl_script.py" 
  source_hash = filemd5("${path.module}/../scripts/glue_etl_script.py")
}

# Captura as subnets da VPC padrão da conta AWS
# Resolução do problema de subnet_id do rds, devido ao aws academy lab criar os recursos em uma VPC padrão
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [aws_security_group.mysql_sg.vpc_id] # Usa a mesma VPC onde seu SG foi criado
  }
  
  # Forçar filtro pela AZ do banco
  filter {
    name   = "availability-zone"
    values = [aws_db_instance.mysql.availability_zone]
  }
}

# DATA SOURCE CORRIGIDO: Busca a tabela de rotas principal da VPC
data "aws_route_table" "default" {
  vpc_id = aws_security_group.mysql_sg.vpc_id

  # Filtra para garantir que vai pegar a tabela de rotas principal (Main) da VPC padrão
  filter {
    name   = "association.main"
    values = ["true"]
  }
}

# ENDPOINT DO S3 UTILIZANDO A TABELA DE ROTAS ENCONTRADA
resource "aws_vpc_endpoint" "s3_endpoint" {
  vpc_id            = aws_security_group.mysql_sg.vpc_id
  service_name      = "com.amazonaws.us-east-1.s3"
  vpc_endpoint_type = "Gateway"

  # Associa o endpoint de forma limpa à tabela de rotas
  route_table_ids = [data.aws_route_table.default.id]
}
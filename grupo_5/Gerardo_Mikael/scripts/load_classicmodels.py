import pymysql
import sqlparse

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SQL_FILE_PATH = BASE_DIR.parent / "sql" / "mysqlsampledatabase.sql"

# Config de acesso
# PyMySQL usa apenas o HOST.
# Recebendo dados no padrão "classicmodels-db.xxxx.us-east-1.rds.amazonaws.com",.

DB_HOST = "classicmodels-db.c4iczixrubp8.us-east-1.rds.amazonaws.com" 
DB_USER = "admin"
DB_PASS = "SENHAFORTEDETESTE"
SQL_FILE_PATH = SQL_FILE_PATH

def execute_sql_file(host, user, password, file_path):
    print("Conectando ao RDS...")
    connection = pymysql.connect(
        host=host,
        user=user,
        password=password,
        autocommit=True,
        client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS
    )
    
    try:
        with connection.cursor() as cursor:
            print("Desativando constraints de chaves estrangeiras...")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            
            print(f"Lendo e parseando o arquivo: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # O sqlparse quebra o arquivo em statements 
            # O objetivo é evitar erros por múltipla statements em um mesmo comando (problema do pymysql)
            statements = sqlparse.split(sql_content)
            print(f"Total de comandos detectados: {len(statements)}")
            
            for index, statement in enumerate(statements):
                cleaned_statement = statement.strip()
                
                if not cleaned_statement:
                    continue
                
                try:
                    # Log
                    if index % 50 == 0:
                        print(f"Executando comando {index}/{len(statements)}...")
                    
                    cursor.execute(cleaned_statement)
                except Exception as e:
                    print(f"\n[ERRO] Falha no comando index {index}:")
                    print(cleaned_statement[:300], "... (truncado)")
                    print(f"Mensagem do MySQL: {e}")
                    raise e
                    
            print("Reativando constraints de chaves estrangeiras...")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
            print("\n[SUCESSO] Carga concluída sem quebras de sintaxe!")
            
    finally:
        connection.close()

if __name__ == "__main__":
    # O RDS deve ter sido criado e estar acessível antes de rodar.
    execute_sql_file(DB_HOST, DB_USER, DB_PASS, SQL_FILE_PATH)
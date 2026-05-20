#Provider block
provider "aws" {
  profile = "default"
  region = "us-east-1"
}

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

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

#Instância RDS MySQL para o banco de dados do projeto

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
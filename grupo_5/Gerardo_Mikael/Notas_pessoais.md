Anotações:

# Estrutura do terraform
A estrutura inicial do terraform conssiste em:
main (núcleo da infra com providers, resources e data sources)
Em resumo o que será criado

variables (entradas parametrizaveis, declara variáveis com tipo e descrição pra reutilização)
regiões, senhas, nomes de buckets, nomes de db

terraform.tfvars (valores reais das variáveis declaradas, não vai pro git) senhas, endpoints, credenciais

outputs (expõe informações após o apply)

# uso do publicly_accessible
Por padrão, uma instância RDS nasce isolada. Para que você consiga rodar os scripts de carga/validação do computador local, o RDS precisará ter a flag publicly_accessible = true
O Security Group dele deve permitir conexões na porta 3306 vinda IP local.

# Ciclo final
O Terraform cria o RDS e S3, obter host pro load, fazer carga dos dados com script Python, o Terraform precisa expor os outputs corretos (o endpoint do banco) para que o script Python saiba onde se conectar.
A estrutura inicial do terraform conssiste em:
main (núcleo da infra com providers, resources e data sources)
Em resumo o que será criado

variables (entradas parametrizaveis, declara variáveis com tipo e descrição pra reutilização)
regiões, senhas, nomes de buckets, nomes de db

terraform.tfvars (valores reais das variáveis declaradas, não vai pro git) senhas, endpoints, credenciais

outputs (expõe informações após o apply)
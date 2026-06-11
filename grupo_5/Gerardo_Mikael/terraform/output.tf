output "rds_endpoint" {
  value = aws_db_instance.mysql.endpoint
}

output "bucket_name" {
  value = aws_s3_bucket.data_lake.bucket
}

output "glue_script_s3_path" {
  value       = "s3://${aws_s3_bucket.data_lake.bucket}/scripts/"
  description = "Pasta do S3 para fazer o upload do script Python"
}
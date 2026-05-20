output "rds_endpoint" {
  value = aws_db_instance.mysql.endpoint
}

output "bucket_name" {
  value = aws_s3_bucket.data_lake.bucket
}
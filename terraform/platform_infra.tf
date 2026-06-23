terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region"       { default = "us-east-1" }
variable "environment"      { default = "production" }
variable "redshift_db_name" { default = "analytics" }

resource "aws_s3_bucket" "data_lake" {
  bucket = "platform-data-lake-${var.environment}"
  tags   = { Environment = var.environment, Team = "platform-engineering" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  rule {
    id     = "iceberg-cleanup"
    status = "Enabled"
    filter { prefix = "iceberg/" }
    expiration { days = 90 }
  }
}

resource "aws_redshift_parameter_group" "main" {
  name   = "platform-redshift-params"
  family = "redshift-1.0"
  parameter { name = "enable_user_activity_logging" value = "true" }
}

resource "aws_redshift_cluster" "main" {
  cluster_identifier           = "platform-redshift-${var.environment}"
  database_name                = var.redshift_db_name
  master_username              = "admin"
  master_password              = var.redshift_password
  node_type                    = "ra3.xlplus"
  number_of_nodes              = 2
  cluster_parameter_group_name = aws_redshift_parameter_group.main.name
  encrypted                    = true
  skip_final_snapshot          = false
  final_snapshot_identifier    = "platform-final-snapshot"
  tags = { Environment = var.environment }
}

resource "aws_rds_cluster" "postgres" {
  cluster_identifier      = "platform-aurora-${var.environment}"
  engine                  = "aurora-postgresql"
  engine_version          = "15.4"
  database_name           = "platform_ops"
  master_username         = "platform_admin"
  master_password         = var.postgres_password
  backup_retention_period = 7
  storage_encrypted       = true
  deletion_protection     = true
  tags = { Environment = var.environment }
}

resource "aws_iam_role" "redshift_s3_role" {
  name = "platform-redshift-s3-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "redshift.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "redshift_s3_policy" {
  name = "redshift-s3-access"
  role = aws_iam_role.redshift_s3_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:ListBucket", "s3:PutObject"]
      Resource = [aws_s3_bucket.data_lake.arn, "${aws_s3_bucket.data_lake.arn}/*"]
    }]
  })
}

output "redshift_endpoint" { value = aws_redshift_cluster.main.endpoint }
output "aurora_endpoint"   { value = aws_rds_cluster.postgres.endpoint }
output "data_lake_bucket"  { value = aws_s3_bucket.data_lake.bucket }

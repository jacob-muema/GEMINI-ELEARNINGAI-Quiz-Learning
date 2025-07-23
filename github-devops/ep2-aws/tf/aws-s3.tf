provider "aws" {
  region = var.aws_region
}

resource "aws_s3_bucket" "static_website" {
  bucket = var.name

  tags = {
    Name        = "gh-action"
    Environment = "dev" # Or your environment
  }
}

resource "aws_s3_bucket_website_configuration" "static_website_config" {
  bucket = aws_s3_bucket.static_website.id

  index_document {
    suffix = "index.html"
  }

  error_document { # Optional
    key = "error.html"
  }
}

resource "aws_s3_bucket_policy" "static_website_policy" {
  depends_on = [
    aws_s3_bucket_public_access_block.static_website_public_access_block,
  ]
  bucket = aws_s3_bucket.static_website.id

  policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::${aws_s3_bucket.static_website.id}/*"
    }
  ]
}
POLICY
}

resource "aws_s3_bucket_public_access_block" "static_website_public_access_block" {
  bucket = aws_s3_bucket.static_website.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_ownership_controls" "s3_ownership_controls" {
  bucket = aws_s3_bucket.static_website.id
  rule {
    object_ownership = "ObjectWriter"
  }
}

resource "aws_s3_bucket_acl" "example" {
  bucket = aws_s3_bucket.static_website.id
  acl    = "public-read"
  depends_on = [
    aws_s3_bucket_policy.static_website_policy,
    aws_s3_bucket_public_access_block.static_website_public_access_block,
    aws_s3_bucket_ownership_controls.s3_ownership_controls
  ]
}

output "website_endpoint" {
  value = aws_s3_bucket_website_configuration.static_website_config.website_endpoint
  description = "The website endpoint of the S3 bucket."
}

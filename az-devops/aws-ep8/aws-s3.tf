# Author: Somnath Das 

provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "mys3" {
  bucket = "dl-azdevops-ep8"
  tags   = {
    channel: "daslearning"
    episode: "ep-8"
    playlist: "azure-devops"
  }
}

resource "aws_s3_bucket_acl" "acl" {
  bucket = aws_s3_bucket.mys3.id
  acl    = "private"
}

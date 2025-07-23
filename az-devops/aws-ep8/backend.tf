terraform {
  backend "s3" {
    bucket = "daslearning-tf"
    key    = "youtube/az-devops/ep8/terraform.tfstate"
    region = "ap-south-1"
  }
}

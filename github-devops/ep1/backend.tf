# backend config

terraform {
  required_version = "~> 1.5"
  backend "gcs" {
    bucket  = "dl-youtube-state"
    prefix  = "terraform/ep1"
  }
}

provider "google" {
  #project = "dl-k8s-dev1cade"
}

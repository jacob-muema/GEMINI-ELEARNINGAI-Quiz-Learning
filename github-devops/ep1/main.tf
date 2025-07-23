# Google reources

resource "google_storage_bucket" "bucket" {
  project  = "dl-k8s-dev1cade"
  name     = "daslearning-bucket-23"
  location = "ASIA-SOUTH1"
}

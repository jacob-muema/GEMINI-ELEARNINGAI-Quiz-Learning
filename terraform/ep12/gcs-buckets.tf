# Create a GCS bucket

resource "google_storage_bucket" "buckets" {
  name     = var.bucket.name
  project  = var.project
  location = var.bucket.region
  labels   = var.bucket.tags
}

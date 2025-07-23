# Create a GCS bucket

resource "google_storage_bucket" "bucket" {
  name     = var.name
  project  = var.project
  location = var.region
  labels   = var.tags
}

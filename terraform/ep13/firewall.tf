# DasLearning Episode no. 13 on Terraform Dynamic Block

resource "google_compute_network" "default" {
  name    = "test-network"
  project = var.project
}

# Only Allow & Ingress for this demo

resource "google_compute_firewall" "static" {
  name        = "static-rule"
  network     = google_compute_network.default.name
  project     = var.project
  description = "A static allow method"

  allow {
    protocol = "icmp"
  }

  allow {
    protocol = "tcp"
    ports    = ["80", "8080", "1000-2000"]
  }

  source_ranges = var.source_ranges
  source_tags   = var.source_tags
  priority      = 1010

  log_config {
    metadata = "INCLUDE_ALL_METADATA"
  }
}

resource "google_compute_firewall" "dynamic" {
  name        = var.name
  network     = google_compute_network.default.name
  project     = var.project
  description = var.description

  dynamic "allow" {
    for_each = var.rules
    content {
      protocol = allow.value.protocol
      ports    = allow.value.ports
    }
  }

  source_ranges = var.source_ranges
  source_tags   = var.source_tags
  priority      = var.priority

  dynamic log_config {
    for_each = var.log_config != "" ? [1] : []
    content {
      metadata = var.log_config
    }
  }
}

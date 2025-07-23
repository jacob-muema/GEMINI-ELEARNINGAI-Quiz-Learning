# The values for the variables

project     = "" # update this
name        = "dynamic-rule"
description = "The dynamic rule"

rules = {
  "web" = {
    ports    = ["80", "8080", "443"]
    protocol = "tcp"
  }
  "custom" = {
    ports    = ["93", "1992-2024"]
    protocol = "tcp"
  }
  "udp" = {
    ports    = ["127-338"]
    protocol = "udp"
  }
  "icmp" = {
    protocol = "icmp"
  }
}

source_ranges = [ "10.10.0.0/24" ]
priority      = 2024

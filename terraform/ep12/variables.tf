# Defines the variables for the episode

variable "project" {
  type        = string
  description = "The Project to deploy the bucket"
}

variable "bucket" {
  type = object({
    name   = string # name of the bucket
    region = optional(string, "europe-west2")
    tags   = optional(map(string), {})
  })
}

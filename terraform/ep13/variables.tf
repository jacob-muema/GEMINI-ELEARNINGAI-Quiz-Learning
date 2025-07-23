# Defines the variables for the episode

variable "name" {
  type        = string
  description = "The name of the firewall rule to be created"
}

variable "project" {
  type        = string
  description = "The Project to deploy the resources"
}

variable "description" {
  type        = string
  description = "The details about the firewall rule"
  default     = ""
}

variable "rules" {
  type = map(object({
    protocol = string
    ports    = optional(list(string), null)
  }))

  description = "The ingress rules to be applied"
  default     = null
}

variable "source_ranges" {
  type        = list(string)
  description = "The list of CIDRs to be allowed"
  default     = []
}

variable "source_tags" {
  type        = list(string)
  description = "The list of source tags to be allowed"
  default     = []
}

variable "priority" {
  type        = number
  description = "The priority of the rule"
  default     = 1000
}

variable "log_config" {
  type        = string
  description = "Set the log config type"
  default     = ""
  validation {
    condition     = contains(["EXCLUDE_ALL_METADATA", "INCLUDE_ALL_METADATA", ""], var.log_config)
    error_message = "The value should be from one of INCLUDE_ALL_METADATA or EXCLUDE_ALL_METADATA"
  }
}

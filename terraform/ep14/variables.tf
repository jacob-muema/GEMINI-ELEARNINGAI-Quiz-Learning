# Variables for EP 14
variable "subscription_id" {
  type        = string
  description = "The Azure Subscription ID"
}

variable "rg_name" {
  type        = string
  description = "The Resource Group name"
}

variable "local_bkt_name" {
  type        = string
  description = "The name of the single bucket for local var example"
}

variable "storage_accounts" {
  type = list(object({
    name                     = string # Storage account name
    location                 = string
    account_tier             = optional(string, "Standard")
    account_replication_type = optional(string, "LRS")
    container_list           = list(string) # List of container names to be created under the storage account
  }))
}

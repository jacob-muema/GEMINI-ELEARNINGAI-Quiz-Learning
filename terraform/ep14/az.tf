# Using Terraform Local Variables & Understanding nested for loop

locals {
  example_stg_acc = "${var.local_bkt_name}local"

  stg_container_mappings = distinct(flatten([
    for stg in var.storage_accounts : [
      for container in stg.container_list : {
        stg_acc        = stg.name
        container_name = container
      }
    ]
  ]))

}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

resource "azurerm_resource_group" "rg" {
  name      = var.rg_name
  location  = "northeurope"
}

resource "azurerm_storage_account" "local_example" {
  name                     = local.example_stg_acc
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_account" "looped_stg_accounts" {
  for_each = { for bkt in var.storage_accounts : bkt.name => bkt }

  resource_group_name      = azurerm_resource_group.rg.name

  name                     = each.key
  location                 = each.value.location
  account_tier             = each.value.account_tier
  account_replication_type = each.value.account_replication_type
}

resource "azurerm_storage_container" "nested_looped_containers" {
  for_each = { for stg_cont in local.stg_container_mappings : "${stg_cont.stg_acc}-${stg_cont.container_name}" => stg_cont }

  name                  = each.value.container_name
  storage_account_id    = azurerm_storage_account.looped_stg_accounts[each.value.stg_acc].id
  container_access_type = "private"
}

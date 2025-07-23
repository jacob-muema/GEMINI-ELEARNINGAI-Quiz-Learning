# Values for the variables

subscription_id = "" # Update with your ID
rg_name         = "rg-dl-tf-ep14"
local_bkt_name  = "dlytep14"

storage_accounts = [
  {
    name           = "dlytep14loop1"
    location       = "eastasia"
    container_list = ["images", "videos", "pdfs"]
  },
  {
    name           = "dlytep14loop2"
    location       = "eastus"
    container_list = ["diagrams", "codes"]
  }
]

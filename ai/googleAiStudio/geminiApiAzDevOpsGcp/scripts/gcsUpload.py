# Upload a file to GCS bucket
# pip install --upgrade google-cloud-storage

from google.cloud import storage
import os
import sys

# Set the bucket context
storage_client = storage.Client()
bucket = storage_client.get_bucket(sys.argv[1]) # Bucket name will be sent from argument no 1
ticket_number = sys.argv[2]

# The uplod path/file_name
blob_tf_code = bucket.blob(f'runid{ticket_number}/main.tf')
blob_tf_state = bucket.blob(f'runid{ticket_number}/terraform.tfstate')
blob_tf_code.upload_from_filename('./main.tf')
blob_tf_state.upload_from_filename('./terraform.tfstate')

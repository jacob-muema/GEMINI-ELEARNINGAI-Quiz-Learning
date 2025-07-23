from gcloud import storage
storage_client = storage.Client()
bucket = storage_client.get_bucket("daslearning-bucket-23")
blob = bucket.blob('tfolder/newtxt.txt')
blob.upload_from_filename('./test.txt')

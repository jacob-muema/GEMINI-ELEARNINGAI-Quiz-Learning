from google import genai # pip install -q -U google-genai
from pydantic import BaseModel, TypeAdapter # pip install pydantic
import os
import json
import sys

g_api_key = os.environ["GEMINI_API_KEY"]

prj_id = sys.argv[1] # Project ID first
usr_prompt = sys.argv[2] # Then the user prompt

defined_word = "Please create a complete terraform script including provider block with given GCP project ID and other details. "
prompt = defined_word + usr_prompt + f"\nGCP Project ID: {prj_id}"

class TfCode(BaseModel):
  tf_code: str


client = genai.Client(api_key=g_api_key)
response = client.models.generate_content(
    model = 'gemini-2.0-flash',
    contents = prompt,
    config={
        'response_mime_type': 'application/json',
        'response_schema': TfCode,
    },
)
# Use the response as a JSON string.
print(response.text)

dic_json =  json.loads(response.text)
tf_code = dic_json['tf_code']

# Create the file
with open('main.tf', "w") as file:
    file.write(tf_code)

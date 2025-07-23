import httpx
import os
import base64
import google.generativeai as genai

genai.configure(api_key="")
model = genai.GenerativeModel(model_name = "gemini-1.5-flash")
image_path_1 = "https://images.nationalgeographic.org/image/upload/t_edhub_resource_key_image/v1638882947/EducationHub/photos/tourists-at-victoria-falls.jpg"  # Replace with the actual path to your first image

image_1 = httpx.get(image_path_1)

prompt = "Tell me about this image."

response = model.generate_content([{'mime_type':'image/jpeg', 'data': base64.b64encode(image_1.content).decode('utf-8')}, prompt])

print(response.text)
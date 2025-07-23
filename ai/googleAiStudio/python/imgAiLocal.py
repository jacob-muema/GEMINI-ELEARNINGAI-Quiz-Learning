import PIL.Image
import os
import google.generativeai as genai

image_path_1 = "test.jpg"  # Replace with the actual path to your first image

sample_file_1 = PIL.Image.open(image_path_1)

genai.configure(api_key="")
#Choose a Gemini model.
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

prompt = "Tell me about this image."

response = model.generate_content([prompt, sample_file_1])

print(response.text)

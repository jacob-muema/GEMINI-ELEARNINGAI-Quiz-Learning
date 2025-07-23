import google.generativeai as genai

genai.configure(api_key="AIzaSyB_P_P2n9EoKrj4IUvGqgm5uenMcCP6Lug")
model = genai.GenerativeModel("gemini-1.5-flash")
response = model.generate_content("What is Reliability Engineeriing?")
print(response.text)

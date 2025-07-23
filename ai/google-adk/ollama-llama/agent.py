from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

ollama_model = LiteLlm(model="ollama_chat/llama3.2")

root_agent = Agent(
    name = "OllamaLocalAgent",
    model = ollama_model,
    description = "An agent powered by Ollama local model",
    instruction = "You are a helpful assistant.",
    tools = []
)

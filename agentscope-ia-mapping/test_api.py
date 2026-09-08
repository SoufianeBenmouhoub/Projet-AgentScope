import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY", "").strip()
if not api_key or api_key == "your_openai_api_key_here":
    raise RuntimeError(
        "OPENAI_API_KEY is missing or still set to the placeholder value. "
        "Add your real key to the .env file."
    )

client = OpenAI(api_key=api_key)

response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=[
        {"role": "user", "content": "Bonjour, réponds-moi en une phrase."}
    ]
)

print(response.choices[0].message.content)
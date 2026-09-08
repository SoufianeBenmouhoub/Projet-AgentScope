from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"  # valeur factice, Ollama n'en a pas besoin mais la bibliothèque l'exige
)

response = client.chat.completions.create(
    model="llama3.2",
    messages=[
        {"role": "user", "content": "Bonjour, réponds-moi en une phrase."}
    ]
)

print(response.choices[0].message.content)
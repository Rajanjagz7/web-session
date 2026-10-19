from google import genai

# Reads the API key from the GEMINI_API_KEY (or GOOGLE_API_KEY) env var.
client = genai.Client()

# "gemini-3.7-flash" isn't a real model id - using a current, known-valid
# one instead. Swap this for whichever model your account has access to.
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Explain how AI works in a few words",
)

print(response.text)

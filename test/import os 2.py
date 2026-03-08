import os
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(override=True)


def call_ollama(message: str = "hi") -> str:
    """Call an OpenAI-compatible Ollama (or other) endpoint using OpenAI client."""
    ollama_base_url = os.getenv("OLLAMA_BASE_URL")
    ollama_model_name = os.getenv("OLLAMA_MODEL_NAME")
    ollama_api_key = os.getenv("OLLAMA_API_KEY") or "not-needed"

    if not ollama_base_url or not ollama_model_name:
        raise RuntimeError("OLLAMA_BASE_URL or OLLAMA_MODEL_NAME is not set in .env")

    client = OpenAI(base_url=ollama_base_url, api_key=ollama_api_key)

    completion = client.chat.completions.create(
        model=ollama_model_name,
        messages=[{"role": "user", "content": message}],
    )

    return completion.choices[0].message.content


def call_gemini(message: str = "hi") -> str:
    """Call a Google Gemini-compatible endpoint via OpenAI client."""
    # Prefer gemini_api_key, fall back to gemini_api_key if set
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    gemini_base_url = os.getenv("GEMINI_BASE_URL")
    gemini_model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")

    if not gemini_api_key:
        raise RuntimeError("GOOGLE_API_KEY or GEMINI_API_KEY is not set in .env")

    client = OpenAI(base_url=gemini_base_url, api_key=gemini_api_key)

    completion = client.chat.completions.create(
        model=gemini_model_name,
        messages=[{"role": "user", "content": message}],
    )

    # Typical OpenAI-style response
    return completion.choices[0].message.content


if __name__ == "__main__":
    # Example usage; change as needed
    try:
        print("OLLAMA:", call_ollama("hi from Ollama"))
    except Exception as e:
        print("Error calling Ollama:", e)

    try:
        print("GEMINI:", call_gemini("hi from Gemini"))
    except Exception as e:
        print("Error calling Gemini:", e)
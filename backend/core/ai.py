from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from core.config import settings

def generate_embedding(text: str) -> List[float]:
    """
    Generates a 768-dimensional vector embedding for the given text using Gemini.
    """
    if not text or not text.strip():
        return []
        
    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=settings.GOOGLE_API_KEY
        )
        return embeddings.embed_query(text)
    except Exception as e:
        print(f"Failed to generate embedding: {e}")
        return []

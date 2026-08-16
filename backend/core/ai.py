from typing import List
from langchain_openai import OpenAIEmbeddings
from core.config import settings

def generate_embedding(text: str) -> List[float]:
    """
    Generates a 1536-dimensional vector embedding for the given text using OpenAI.
    """
    if not text or not text.strip():
        return []
        
    try:
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=settings.OPENAI_API_KEY
        )
        return embeddings.embed_query(text)
    except Exception as e:
        print(f"Failed to generate embedding: {e}. Falling back to mock embeddings for demonstration.")
        import random
        # Return a mock 1536-dimensional vector so semantic search doesn't break
        return [random.random() for _ in range(1536)]

def generate_cover_letter(profile_dict: dict, job_title: str, job_company: str, job_desc: str) -> str:
    """
    Generates a tailored cover letter using the new Google Gemini SDK (gemini-3.6-flash).
    """
    from google import genai
    
    if not settings.GOOGLE_API_KEY:
        return "MOCK COVER LETTER: Please add a GOOGLE_API_KEY to your .env to generate real cover letters."
        
    try:
        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        
        prompt = (
            "You are an expert career coach writing a highly tailored, professional cover letter.\n"
            f"The user is applying for the role of '{job_title}' at '{job_company}'.\n\n"
            f"Job Description Context:\n{job_desc[:1000]}\n\n"
            f"User Profile Details:\n{profile_dict}\n\n"
            "Write a concise (max 3-4 paragraphs) cover letter that connects the user's skills and experience to the job requirements. "
            "Keep it professional, engaging, and ready to send. Output ONLY the cover letter text, no intro or outro."
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        return response.text
    except Exception as e:
        print(f"Failed to generate cover letter: {e}")
        return f"MOCK COVER LETTER: Generating failed due to an API error ({e})."

def extract_jobs_from_text(page_text: str, base_url: str, user_profile: dict) -> list:
    """
    Uses Gemini to intelligently extract job listings from raw page text/links.
    Returns a list of dicts: [{"title": "...", "job_url": "...", "location": "...", "salary_range": "...", "description": "..."}]
    """
    from google import genai
    import json
    
    if not settings.GOOGLE_API_KEY:
        print("Missing GOOGLE_API_KEY for extraction.")
        return []
        
    try:
        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        
        prompt = (
            "You are an expert data extractor. I am providing you with the text content of a career page.\n"
            f"The base URL of this page is: {base_url}\n"
            f"The user is looking for roles related to: {user_profile.get('preferred_roles', 'Software Engineer')}\n\n"
            "Extract all job listings from the text that match the user's preferred roles. "
            "For each job, extract:\n"
            "- 'title': The job title\n"
            "- 'company': The hiring company's actual name (not the job board or source URL). Distinguish the real hiring company from the generic portal.\n"
            "- 'job_url': The precise, specific absolute URL to apply for THIS individual job. Match the job title with the exact href from the PAGE LINKS. If you absolutely cannot find a specific link, return null.\n"
            "- 'location': The job location\n"
            "- 'salary_range': The salary range if mentioned, else 'Undisclosed'\n"
            "- 'description': A short 1-2 sentence description if available, else 'Discovered via AI Scraper'\n"
            "- 'confidence': A float between 0.0 and 1.0 indicating your confidence in this extraction based on data completeness and clarity.\n\n"
            "Return the result ONLY as a raw JSON array of objects. Do not wrap it in markdown block quotes (```json) or any other text.\n\n"
            f"Page Content:\n{page_text[:30000]}" # Truncate to avoid context window limits
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        # Parse the JSON response
        response_text = response.text.strip()
        # Clean up any potential markdown formatting the AI might add despite instructions
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        jobs = json.loads(response_text.strip())
        if isinstance(jobs, list):
            return jobs
        return []
    except Exception as e:
        print(f"Failed to extract jobs with AI: {e}")
        return []

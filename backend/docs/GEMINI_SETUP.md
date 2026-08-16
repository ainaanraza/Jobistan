# Google Gemini SDK Setup Guide

This document outlines the correct configuration and usage pattern for the Google Gemini API within the Jobistan backend.

## Environment Variables

Ensure your `.env` file has the following variable:
```env
GOOGLE_API_KEY=your_actual_api_key_here
```

## Package Name & Installation

The application uses the modern Google GenAI SDK. 

**Correct Package:** `google-genai`
**Installed Version:** `^2.17.0` (or latest compatible)

**CRITICAL WARNING:** 
Do **NOT** install `google-generativeai`. Installing both packages simultaneously causes a namespace collision in the `google` module, resulting in the following fatal crash:
`ImportError: cannot import name 'genai' from 'google' (unknown location)`

If you encounter this error, clean your environment:
```bash
pip uninstall -y google-genai google-generativeai
pip install google-genai
```

## Standard Import Syntax

Always use the following import syntax:
```python
from google import genai
```

Never use `import google.generativeai as genai`.

## Client Initialization

The modern SDK uses a `Client` instantiation pattern instead of global configuration.

### Correct Pattern:
```python
from google import genai
from core.config import settings

client = genai.Client(api_key=settings.GOOGLE_API_KEY)

# Generate Content Example
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Tell me a joke."
)

print(response.text)
```

### Incorrect / Legacy Pattern (DO NOT USE):
```python
import google.generativeai as genai
genai.configure(api_key=...)
model = genai.GenerativeModel("gemini-pro")
response = model.generate_content("...")
```

## Docker Configuration

If the backend is deployed via Docker, ensure that the `Dockerfile` correctly installs `google-genai`. If a namespace collision occurs inside the container, you must rebuild the image using `--no-cache` to purge the corrupted `site-packages` directory:

```bash
docker-compose build --no-cache backend
```

## Troubleshooting Local Environments

1. **Shadowing Modules**: Ensure there are no local files named `google.py`, `genai.py`, or folders named `google/` in the root of the project. This will shadow the actual package.
2. **Virtual Environment Mismatch**: Ensure the terminal you are using to run `uvicorn` has the correct `venv` activated (e.g. `(venv) PS D:\jobfinder\Jobistan\backend>`).

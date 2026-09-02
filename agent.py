import os
import json
from google import genai
from PIL import Image

def process_query(query: str, file_metadata: dict) -> dict:
    """
    Agentic controller that uses Gemini to analyze images and answer queries.
    It returns a JSON response containing the task name, model used, and response.
    """
    # Initialize the Gemini client securely from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    client = genai.Client(api_key=api_key)
    
    system_prompt = (
        "You are an expert remote sensing AI assistant for SatQuery AI. "
        "You will receive a user query and one or more satellite images. "
        "Your job is to analyze the images and directly answer the query.\n\n"
        "You MUST respond with ONLY a valid JSON object matching this schema:\n"
        "{\n"
        "  \"task_name\": \"[E.g., Single-Image VQA, Change Detection, etc.]\",\n"
        "  \"model_used\": \"gemini-3.6-flash\",\n"
        "  \"response\": \"[Your detailed answer based on the images]\"\n"
        "}"
    )
    
    # Prepare the contents to send to Gemini
    contents = [system_prompt, f"User Query: {query}"]
    
    # Add all uploaded images to the prompt
    for uploaded_file in file_metadata.get("files", []):
        try:
            # Save position, read for PIL, restore position
            pos = uploaded_file.tell()
            uploaded_file.seek(0)
            img = Image.open(uploaded_file)
            # Make a copy in memory so we don't hold the file lock
            img.load()
            contents.append(img)
            uploaded_file.seek(pos)
        except Exception as e:
            print(f"Failed to load image for Gemini: {e}")

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=contents,
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        
        parsed_json = json.loads(response.text)
        
        # Map fields to what app.py expects, plus the new ones
        return {
            "selected_task": parsed_json.get("task_name", "N/A"),
            "tools_used": parsed_json.get("model_used", "gemini-3.6-flash"),
            "confidence_score": "High", # Gemini doesn't output confidence score natively
            "reasoning": parsed_json.get("response", ""),
            "modality": file_metadata.get("modality", "Unknown")
        }
        
    except json.JSONDecodeError:
        return {
            "selected_task": "Error",
            "tools_used": "None",
            "confidence_score": "0%",
            "reasoning": "The LLM failed to return a valid JSON object.",
            "modality": file_metadata.get("modality", "Unknown")
        }
    except Exception as e:
        raise Exception(f"Gemini API Error: {str(e)}")

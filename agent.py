import os
import json
from google import genai
from PIL import Image
from utils import preprocess_raster_for_vision

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
        "You will receive a user query and one or more preprocessed satellite images (scaled to 8-bit RGB). "
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
    
    # Preprocess all uploaded images and append to prompt
    for uploaded_file in file_metadata.get("files", []):
        try:
            arr, meta = preprocess_raster_for_vision(uploaded_file)
            if arr is not None:
                # Convert processed numpy array to PIL Image for Gemini
                img = Image.fromarray(arr)
                contents.append(img)
                contents.append(f"Metadata for above image: {meta}")
        except Exception as e:
            print(f"Failed to preprocess image for Gemini: {e}")

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

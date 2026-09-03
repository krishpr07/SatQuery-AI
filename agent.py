import os
import json
import time
from google import genai
from tools import (
    tool_single_image_vqa,
    tool_visual_grounding,
    tool_change_detection,
    tool_optical_sar_fusion
)
from utils import preprocess_raster_for_vision

def process_query(query: str, file_metadata: dict, chat_history: list = None) -> dict:
    """
    Authentic 2-Stage Agentic Router.
    Stage 1: Intent Routing via LLM to select tool and parameters.
    Stage 2: Deterministic execution of the selected algorithm.
    """
    start_time = time.time()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    client = genai.Client(api_key=api_key)
    
    # Preprocess images
    processed_images = []
    meta_list = []
    for uploaded_file in file_metadata.get("files", []):
        try:
            arr, meta = preprocess_raster_for_vision(uploaded_file)
            if arr is not None:
                processed_images.append(arr)
                meta_list.append(meta)
        except Exception as e:
            print(f"Preprocessing error: {e}")
            
    num_images = len(processed_images)
    
    # --- STAGE 1: Intent & Parameter Routing ---
    history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in (chat_history or [])])
    
    routing_prompt = f"""
    You are Stage 1 of an Agentic Remote Sensing Orchestrator.
    Determine the correct tool to use based on the user's query, chat history, and number of available images ({num_images}).
    
    Available tools:
    - tool_single_image_vqa: General Q&A about an image.
    - tool_visual_grounding: Detects and draws bounding boxes around objects. Requires parameter 'target_phrase'.
    - tool_change_detection: Requires 2 images. Computes change heatmaps over time.
    - tool_optical_sar_fusion: Requires 2 images. Fuses Optical and SAR textures.
    
    Chat History:
    {history_str}
    
    User Query: {query}
    
    Return EXACTLY this JSON format (no other text):
    {{
        "tool": "tool_name",
        "parameters": {{"target_phrase": "extracted phrase if visual grounding"}} 
    }}
    """
    
    try:
        route_response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=[routing_prompt],
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0
            )
        )
        route_data = json.loads(route_response.text)
        selected_tool = route_data.get("tool", "tool_single_image_vqa")
        params = route_data.get("parameters", {})
    except Exception as e:
        print(f"Routing Error: {e}")
        selected_tool = "tool_single_image_vqa"
        params = {}
        
    # --- STAGE 2: Tool Execution ---
    response_text = "Error in tool execution."
    confidence = 0.0
    output_image = None
    task_type = "Unknown"
    
    meta_context = meta_list[0] if meta_list else {}
    
    try:
        if selected_tool == "tool_visual_grounding" and num_images >= 1:
            target = params.get("target_phrase", query)
            response_text, confidence, output_image = tool_visual_grounding(processed_images[0], meta_context, target)
            task_type = "Visual Grounding"
        elif selected_tool == "tool_change_detection" and num_images >= 2:
            response_text, confidence, output_image = tool_change_detection(processed_images[0], processed_images[1], meta_list)
            task_type = "Change Detection"
        elif selected_tool == "tool_optical_sar_fusion" and num_images >= 2:
            response_text, confidence, output_image = tool_optical_sar_fusion(processed_images[0], processed_images[1], meta_list)
            task_type = "Cross-Modal Fusion"
        else:
            selected_tool = "tool_single_image_vqa"
            if num_images >= 1:
                response_text, confidence, output_image = tool_single_image_vqa(processed_images[0], meta_context, query)
                task_type = "VQA"
            else:
                response_text = "No valid images to process."
                task_type = "Error"
    except Exception as e:
        response_text = f"Tool '{selected_tool}' execution failed: {str(e)}"
        task_type = "Execution Error"
        
    latency = round(time.time() - start_time, 2)
    
    # Construct authentic ExecutionTrace
    trace = {
        "task_type": task_type,
        "tool_called": selected_tool,
        "parameters": params,
        "latency_seconds": latency,
        "confidence_score": round(confidence, 2)
    }
    
    return {
        "response": response_text,
        "trace": trace,
        "output_image": output_image
    }

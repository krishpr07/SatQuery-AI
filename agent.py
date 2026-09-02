from tools import (
    tool_single_image_vqa,
    tool_change_detection,
    tool_optical_sar_fusion,
    tool_bigearthnet_vlm
)

def process_query(query: str, file_metadata: dict) -> dict:
    """
    Agentic controller that classifies the task based on the user's query 
    and routes it to the appropriate mock specialist tool.
    """
    query_lower = query.lower()
    modality = file_metadata.get("modality", "Unknown")
    
    # 1. Classification & Routing Logic
    if "change" in query_lower or "difference" in query_lower or "compare" in query_lower:
        task = "Change Detection"
        tool_func = tool_change_detection
        tool_name = "tool_change_detection (Mock)"
    elif "fuse" in query_lower or "fusion" in query_lower or "cross-modal" in query_lower:
        task = "Cross-Modal Fusion"
        tool_func = tool_optical_sar_fusion
        tool_name = "tool_optical_sar_fusion (Mock)"
    elif "bigearth" in query_lower or "classification" in query_lower:
        task = "Multi-label Classification"
        tool_func = tool_bigearthnet_vlm
        tool_name = "tool_bigearthnet_vlm (Mock)"
    else:
        task = "Visual Question Answering"
        tool_func = tool_single_image_vqa
        tool_name = "tool_single_image_vqa (Mock)"

    # 2. Tool Execution
    # In a real app, we would pass the actual image arrays/bytes.
    # Here we just pass the metadata and query to our mock tools.
    response, confidence = tool_func(file_metadata["files"], query)

    # 3. Format Output
    return {
        "response": response,
        "task": task,
        "tool_used": tool_name,
        "modality": modality,
        "confidence": confidence
    }

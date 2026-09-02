# Mock Specialist Tools for SatQuery AI

def tool_single_image_vqa(images, query):
    """
    Simulates a Vision-Language Model answering a question about a single image.
    """
    mock_response = f"**Mock VQA Output:** Based on the imagery provided, the answer to '{query}' is that there is predominantly agricultural land visible with scattered residential structures."
    mock_confidence = 0.88
    return mock_response, mock_confidence

def tool_change_detection(images, query):
    """
    Simulates a Bi-temporal change detection model.
    """
    if len(images) < 2:
        return "**Error:** Change detection requires at least two images.", 0.0
    
    mock_response = "**Mock Change Detection Output:** Analysis of the bi-temporal images indicates that built-up area has increased by approximately 15%, while vegetation cover has decreased."
    mock_confidence = 0.92
    return mock_response, mock_confidence

def tool_optical_sar_fusion(images, query):
    """
    Simulates cross-modal fusion (e.g., Optical + SAR).
    """
    mock_response = "**Mock Fusion Output:** Fusing the optical and SAR inputs reveals features obscured by clouds in the optical image, confirming the presence of a new road network."
    mock_confidence = 0.85
    return mock_response, mock_confidence

def tool_bigearthnet_vlm(images, query):
    """
    Simulates a specialized model trained on BigEarthNet for multi-label scene classification.
    """
    mock_response = "**Mock BigEarthNet Output:** The scene is classified with the following labels: 'Arable land', 'Broad-leaved forest', 'Complex cultivation patterns'."
    mock_confidence = 0.95
    return mock_response, mock_confidence

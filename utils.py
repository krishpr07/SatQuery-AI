import os
import rasterio
from PIL import Image

def is_valid_image(uploaded_file):
    """Basic validation to check if file can be opened."""
    try:
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext in ['.tif', '.tiff']:
            # For prototype, we might just mock the rasterio check as file-like objects 
            # from streamlit might need to be read to bytes first, but we can do a simple check.
            pass
        elif ext in ['.png', '.jpg', '.jpeg']:
            Image.open(uploaded_file).verify()
        return True
    except Exception:
        return False

def inspect_files(uploaded_files):
    """
    Inspect uploaded files to determine the input configuration.
    Returns a dictionary with status, modality, and the files.
    """
    if not uploaded_files:
        return {"status": "invalid", "message": "No files uploaded."}

    valid_files = []
    for f in uploaded_files:
        if is_valid_image(f):
            valid_files.append(f)
        else:
            return {"status": "invalid", "message": f"Unsupported or corrupt file: {f.name}"}

    num_files = len(valid_files)
    
    # Simple logic to determine modality based on filenames and count
    filenames = [f.name.lower() for f in valid_files]
    
    modality = "Unknown"
    
    if num_files == 1:
        if "sar" in filenames[0]:
            modality = "Single Image (SAR)"
        else:
            modality = "Single Image (Optical/Multispectral)"
    elif num_files == 2:
        has_sar = any("sar" in name for name in filenames)
        has_opt = any("opt" in name or "rgb" in name for name in filenames)
        
        if has_sar and has_opt:
            modality = "Cross-modal pair (Optical + SAR)"
        else:
            modality = "Bi-temporal pair (Two images)"
    else:
        modality = f"Multi-image collection ({num_files} images)"

    return {
        "status": "valid",
        "modality": modality,
        "files": valid_files,
        "num_files": num_files
    }

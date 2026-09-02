import os
import rasterio
from rasterio.io import MemoryFile
from PIL import Image

def extract_metadata(uploaded_file):
    """Extract metadata using rasterio for GeoTIFFs or Pillow for other images."""
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    metadata = {"name": uploaded_file.name, "format": ext}
    
    try:
        # Save current position
        pos = uploaded_file.tell()
        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()
        uploaded_file.seek(pos)
        
        if ext in ['.tif', '.tiff']:
            with MemoryFile(file_bytes) as memfile:
                with memfile.open() as dataset:
                    metadata["width"] = dataset.width
                    metadata["height"] = dataset.height
                    metadata["bands"] = dataset.count
                    metadata["crs"] = str(dataset.crs) if dataset.crs else "Unknown"
                    metadata["type"] = "GeoTIFF"
        elif ext in ['.png', '.jpg', '.jpeg']:
            image = Image.open(uploaded_file)
            metadata["width"] = image.width
            metadata["height"] = image.height
            metadata["mode"] = image.mode
            metadata["format"] = image.format
            metadata["type"] = "Standard Image"
            
        return metadata
    except Exception as e:
        return {"name": uploaded_file.name, "error": str(e), "type": "Unknown"}

def inspect_files(uploaded_files):
    """
    Inspect uploaded files to determine the input configuration and extract metadata.
    Returns a dictionary with status, modality, and the file metadata.
    """
    if not uploaded_files:
        return {"status": "invalid", "message": "No files uploaded."}

    valid_files_meta = []
    for f in uploaded_files:
        meta = extract_metadata(f)
        if "error" in meta:
            return {"status": "invalid", "message": f"Unsupported or corrupt file: {f.name} ({meta['error']})"}
        valid_files_meta.append(meta)

    num_files = len(valid_files_meta)
    filenames = [m["name"].lower() for m in valid_files_meta]
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
        "files": uploaded_files,
        "metadata": valid_files_meta,
        "num_files": num_files
    }

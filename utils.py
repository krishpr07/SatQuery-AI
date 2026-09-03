import os
import io
import datetime
import numpy as np
import rasterio
from rasterio.io import MemoryFile
from PIL import Image
import tifffile

def calculate_iou(b1, b2):
    """Calculate Intersection over Union (IoU) for two rasterio BoundingBoxes."""
    left = max(b1.left, b2.left)
    bottom = max(b1.bottom, b2.bottom)
    right = min(b1.right, b2.right)
    top = min(b1.top, b2.top)
    
    if right <= left or top <= bottom:
        return 0.0
    
    inter_area = (right - left) * (top - bottom)
    b1_area = (b1.right - b1.left) * (b1.top - b1.bottom)
    b2_area = (b2.right - b2.left) * (b2.top - b2.bottom)
    union_area = b1_area + b2_area - inter_area
    return inter_area / union_area if union_area > 0 else 0.0

def validate_pair_compatibility(meta1, meta2):
    """Rigorous pair compatibility checking for spatial and temporal data."""
    warnings = []
    
    # Check CRS
    crs1 = meta1.get("crs")
    crs2 = meta2.get("crs")
    if crs1 and crs2 and crs1 != crs2:
        warnings.append(f"CRS mismatch: {crs1} vs {crs2}")
        
    # Check Resolution
    res1 = meta1.get("res")
    res2 = meta2.get("res")
    if res1 and res2 and res1[0] > 0 and res2[0] > 0:
        ratio = max(res1[0], res2[0]) / min(res1[0], res2[0])
        if ratio > 3.0:
            warnings.append(f"Resolution difference is > 3x ({res1[0]:.2f} vs {res2[0]:.2f})")
            
    # Check Spatial Overlap
    bounds1 = meta1.get("bounds")
    bounds2 = meta2.get("bounds")
    if bounds1 and bounds2 and crs1 == crs2:
        iou = calculate_iou(bounds1, bounds2)
        if iou < 0.3:
            warnings.append(f"Spatial overlap (IoU) is poor: {iou:.2f}. Bounding boxes might barely intersect.")
            
    # Temporal Gap (if DateTime is available)
    dt1 = meta1.get("datetime")
    dt2 = meta2.get("datetime")
    if dt1 and dt2:
        try:
            # typical format: "YYYY:MM:DD HH:MM:SS"
            d1 = datetime.datetime.strptime(dt1, "%Y:%m:%d %H:%M:%S")
            d2 = datetime.datetime.strptime(dt2, "%Y:%m:%d %H:%M:%S")
            delta = abs((d2 - d1).days)
            meta1["temporal_gap_days"] = delta  # Just store it in meta for trace UI
        except ValueError:
            pass
            
    return warnings

def preprocess_raster_for_vision(uploaded_file):
    """Preprocesses a raster file (Optical/SAR) to an 8-bit array suitable for VLMs."""
    pos = uploaded_file.tell()
    uploaded_file.seek(0)
    file_bytes = uploaded_file.read()
    uploaded_file.seek(pos)
    
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if ext in ['.png', '.jpg', '.jpeg']:
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        return np.array(img), {"type": "Standard Image", "format": ext}
        
    try:
        with MemoryFile(file_bytes) as memfile:
            with memfile.open() as src:
                arr = src.read() # shape: (bands, height, width)
                count = src.count
                meta = {
                    "crs": str(src.crs),
                    "transform": src.transform,
                    "bounds": src.bounds,
                    "res": src.res
                }
                
                # SAR Processing (1-2 bands)
                if count <= 2:
                    band = arr[0].astype(np.float32)
                    # Heuristic for linear vs decibel
                    if np.nanmin(band) >= 0 and np.nanmax(band) < 5000: 
                        band = 10 * np.log10(band + 1e-8)
                        
                    # 2nd to 98th percentile stretch
                    p2, p98 = np.nanpercentile(band, (2, 98))
                    if p98 > p2:
                        stretched = np.clip((band - p2) / (p98 - p2) * 255, 0, 255).astype(np.uint8)
                    else:
                        stretched = np.zeros_like(band, dtype=np.uint8)
                    
                    rgb_arr = np.stack([stretched, stretched, stretched], axis=-1)
                    return rgb_arr, meta
                    
                # Multispectral Processing (>= 4 bands)
                elif count >= 4:
                    # Assumes Blue=1, Green=2, Red=3, NIR=4
                    blue, green, red, nir = [arr[i].astype(np.float32) for i in range(4)]
                    
                    # Compute NDVI
                    denominator = (nir + red + 1e-8)
                    ndvi = np.where(denominator != 0, (nir - red) / denominator, 0)
                    
                    # Normalize RGB for vision
                    rgb = np.stack([red, green, blue], axis=-1)
                    p2, p98 = np.nanpercentile(rgb, (2, 98))
                    
                    if p98 > p2:
                        rgb_stretched = np.clip((rgb - p2) / (p98 - p2) * 255, 0, 255).astype(np.uint8)
                    else:
                        rgb_stretched = np.zeros_like(rgb, dtype=np.uint8)
                    
                    meta["has_ndvi"] = True
                    meta["ndvi_mean"] = float(np.nanmean(ndvi))
                    return rgb_stretched, meta
                
                # Optical RGB Processing (3 bands)
                else:
                    rgb = np.transpose(arr[:3], (1, 2, 0)).astype(np.float32)
                    p2, p98 = np.nanpercentile(rgb, (2, 98))
                    if p98 > p2:
                        rgb_stretched = np.clip((rgb - p2) / (p98 - p2) * 255, 0, 255).astype(np.uint8)
                    else:
                        rgb_stretched = np.zeros_like(rgb, dtype=np.uint8)
                    return rgb_stretched, meta
                    
    except Exception as e:
        print(f"Rasterio read error: {e}")
        try:
            img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            return np.array(img), {"type": "Fallback Image", "error": str(e)}
        except Exception:
            return None, {"error": "Failed to read image data"}

def extract_metadata(uploaded_file):
    """Extracts genuine metadata for sensor detection."""
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    metadata = {"name": uploaded_file.name, "format": ext}
    
    pos = uploaded_file.tell()
    uploaded_file.seek(0)
    file_bytes = uploaded_file.read()
    uploaded_file.seek(pos)
    
    if ext in ['.tif', '.tiff']:
        try:
            with MemoryFile(file_bytes) as memfile:
                with memfile.open() as dataset:
                    metadata["width"] = dataset.width
                    metadata["height"] = dataset.height
                    metadata["bands"] = dataset.count
                    metadata["crs"] = str(dataset.crs) if dataset.crs else "Unknown"
                    metadata["bounds"] = dataset.bounds
                    metadata["res"] = dataset.res
                    metadata["dtypes"] = [str(dt) for dt in dataset.dtypes]
                    
                    count = dataset.count
                    dtype = metadata["dtypes"][0]
                    if count <= 2 and dtype in ['float32', 'uint16']:
                        metadata["modality_guess"] = "SAR"
                    elif count >= 4:
                        metadata["modality_guess"] = "Optical Multispectral"
                    elif count == 3:
                        metadata["modality_guess"] = "Optical RGB"
                    else:
                        metadata["modality_guess"] = "Unknown GeoTIFF"
                        
            try:
                with tifffile.TiffFile(io.BytesIO(file_bytes)) as tif:
                    tags = tif.pages[0].tags
                    if 'DateTime' in tags:
                        metadata['datetime'] = tags['DateTime'].value
            except Exception:
                pass
                
        except Exception as e:
            metadata["error"] = str(e)
            metadata["modality_guess"] = "Corrupt/Unreadable"
    elif ext in ['.png', '.jpg', '.jpeg']:
        try:
            image = Image.open(io.BytesIO(file_bytes))
            metadata["width"] = image.width
            metadata["height"] = image.height
            metadata["mode"] = image.mode
            metadata["modality_guess"] = "Standard Image"
        except Exception as e:
            metadata["error"] = str(e)
            
    return metadata

def inspect_files(uploaded_files):
    if not uploaded_files:
        return {"status": "invalid", "message": "No files uploaded."}

    valid_files_meta = []
    for f in uploaded_files:
        meta = extract_metadata(f)
        if "error" in meta and not meta.get("width"):
            return {"status": "invalid", "message": f"Unsupported or corrupt file: {meta['name']} ({meta['error']})"}
        valid_files_meta.append(meta)

    num_files = len(valid_files_meta)
    modality = "Unknown"
    warnings = []
    
    if num_files == 1:
        modality = f"Single Image ({valid_files_meta[0].get('modality_guess', 'Unknown')})"
    elif num_files == 2:
        m1 = valid_files_meta[0].get("modality_guess", "")
        m2 = valid_files_meta[1].get("modality_guess", "")
        
        if ("SAR" in m1 and "Optical" in m2) or ("Optical" in m1 and "SAR" in m2):
            modality = "Cross-modal pair (Optical + SAR)"
        else:
            modality = "Bi-temporal pair"
            
        warnings = validate_pair_compatibility(valid_files_meta[0], valid_files_meta[1])
    else:
        modality = f"Multi-image collection ({num_files} images)"

    return {
        "status": "valid",
        "modality": modality,
        "files": uploaded_files,
        "metadata": valid_files_meta,
        "num_files": num_files,
        "compatibility_warnings": warnings
    }

def tile_raster(image_array, metadata=None, tile_size=512, overlap=64):
    """
    Generates overlapping tiles for large imagery to prevent OOM errors.
    """
    if metadata is None:
        metadata = {}
        
    h, w = image_array.shape[:2]
    
    if h <= 1024 and w <= 1024:
        metadata["tiles_coords"] = [(0, 0, h, w)]
        metadata["original_shape"] = image_array.shape
        return [image_array]
        
    stride = tile_size - overlap
    tiles = []
    coords = []
    
    for y in range(0, h, stride):
        for x in range(0, w, stride):
            y_end = min(y + tile_size, h)
            x_end = min(x + tile_size, w)
            
            tile = image_array[y:y_end, x:x_end]
            tiles.append(tile)
            coords.append((y, x, y_end, x_end))
            
    metadata["tiles_coords"] = coords
    metadata["original_shape"] = image_array.shape
    return tiles

def stitch_tiles(tiles, metadata):
    """
    Stitches overlapping tiles back into the full georeferenced canvas.
    """
    coords = metadata.get("tiles_coords", [])
    original_shape = metadata.get("original_shape", (0, 0))
    
    if not coords or not tiles:
        return None
        
    h, w = original_shape[:2]
    channels = tiles[0].shape[2] if len(tiles[0].shape) > 2 else 1
    
    if channels > 1:
        canvas = np.zeros((h, w, channels), dtype=np.float32)
    else:
        canvas = np.zeros((h, w), dtype=np.float32)
        
    counts = np.zeros((h, w), dtype=np.float32)
    
    for tile, (y, x, y_end, x_end) in zip(tiles, coords):
        if channels > 1:
            canvas[y:y_end, x:x_end, :] += tile
        else:
            canvas[y:y_end, x:x_end] += tile
            
        counts[y:y_end, x:x_end] += 1
        
    counts[counts == 0] = 1
    
    if channels > 1:
        canvas /= counts[..., np.newaxis]
    else:
        canvas /= counts
        
    return canvas.astype(tiles[0].dtype)

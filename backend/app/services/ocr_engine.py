"""
OCR Engine - Image Processing and Text Extraction
"""
import io
import logging
import cv2
import numpy as np
from PIL import Image
from typing import Tuple, List, Union

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    
try:
    from pdf2image import convert_from_bytes
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    convert_from_bytes = None

logger = logging.getLogger(__name__)


def detect_and_crop_card(image: np.ndarray) -> np.ndarray:
    """
    Detect a rectangular card (KTP, passport etc.) in a photo and crop to it.
    This handles photos where the card sits on a table/surface.
    """
    h, w = image.shape[:2]
    
    # Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Blur to reduce noise, then Canny edge detection
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 30, 150)
    
    # Dilate edges to connect broken lines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    edges = cv2.dilate(edges, kernel, iterations=2)
    
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return image
    
    # Sort by area, largest first
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    
    img_area = h * w
    
    for contour in contours[:5]:  # Check top 5 largest contours
        area = cv2.contourArea(contour)
        
        # Card should be at least 5% of image but less than 95%
        if area < img_area * 0.05 or area > img_area * 0.95:
            continue
        
        # Approximate contour to polygon
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        
        # A card should have 4 corners (rectangle)
        if len(approx) == 4:
            # Use perspective transform to get a straight crop
            pts = approx.reshape(4, 2).astype(np.float32)
            
            # Order points: top-left, top-right, bottom-right, bottom-left
            rect = _order_points(pts)
            
            # Compute width and height of the new image
            widthA = np.linalg.norm(rect[2] - rect[3])
            widthB = np.linalg.norm(rect[1] - rect[0])
            maxWidth = int(max(widthA, widthB))
            
            heightA = np.linalg.norm(rect[1] - rect[2])
            heightB = np.linalg.norm(rect[0] - rect[3])
            maxHeight = int(max(heightA, heightB))
            
            if maxWidth < 100 or maxHeight < 100:
                continue
            
            dst = np.array([
                [0, 0],
                [maxWidth - 1, 0],
                [maxWidth - 1, maxHeight - 1],
                [0, maxHeight - 1]
            ], dtype=np.float32)
            
            M = cv2.getPerspectiveTransform(rect, dst)
            warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
            
            logger.info(f"Card detected and cropped: {maxWidth}x{maxHeight} from {w}x{h}")
            return warped
        
        # Fallback: use bounding rect if we can't find 4 corners
        if len(approx) >= 4 and area > img_area * 0.10:
            x, y, bw, bh = cv2.boundingRect(contour)
            # Add small padding
            pad = 10
            x = max(0, x - pad)
            y = max(0, y - pad)
            bw = min(w - x, bw + 2 * pad)
            bh = min(h - y, bh + 2 * pad)
            
            cropped = image[y:y+bh, x:x+bw]
            logger.info(f"Card bounding box crop: {bw}x{bh} from {w}x{h}")
            return cropped
    
    return image


def _order_points(pts: np.ndarray) -> np.ndarray:
    """Order 4 points as: top-left, top-right, bottom-right, bottom-left"""
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]   # top-left has smallest sum
    rect[2] = pts[np.argmax(s)]   # bottom-right has largest sum
    d = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(d)]   # top-right has smallest diff
    rect[3] = pts[np.argmax(d)]   # bottom-left has largest diff
    return rect


def auto_rotate_image(image: np.ndarray) -> np.ndarray:
    """
    Detect and correct image rotation.
    Strategy:
    1. If portrait orientation (h > w*1.2), rotate 90° CCW (cards are landscape)
    2. Try Tesseract OSD for fine adjustment
    3. Fallback: brute-force between 0° and 180° (upside-down check)
    """
    h, w = image.shape[:2]
    
    # Step 1: Aspect ratio heuristic - ID cards are landscape
    if h > w * 1.2:
        logger.info(f"Portrait orientation detected ({w}x{h}), rotating 90 CCW")
        image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        h, w = image.shape[:2]
    
    # Step 2: Try OSD for fine rotation (0 vs 180)
    try:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        osd = pytesseract.image_to_osd(gray, output_type=pytesseract.Output.DICT)
        angle = osd.get('rotate', 0)
        
        if angle == 180:
            logger.info(f"OSD detected upside-down, rotating 180")
            return cv2.rotate(image, cv2.ROTATE_180)
        elif angle == 90:
            return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        elif angle == 270:
            return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        
        return image
    except Exception as e:
        logger.warning(f"OSD rotation detection failed: {e}, trying brute-force rotation")
        return auto_rotate_bruteforce(image)


def auto_rotate_bruteforce(image: np.ndarray) -> np.ndarray:
    """
    Try all 4 rotations and pick the one that produces the most readable text.
    Uses a quick OCR pass to score each rotation.
    """
    rotations = [
        ("0", image),
        ("90", cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)),
        ("180", cv2.rotate(image, cv2.ROTATE_180)),
        ("270", cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)),
    ]
    
    best_score = -1
    best_image = image
    best_angle = "0"
    
    for angle, rotated in rotations:
        try:
            # Quick OCR on a downscaled version
            h, w = rotated.shape[:2]
            small = cv2.resize(rotated, (w // 2, h // 2))
            if len(small.shape) == 3:
                small = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            text = pytesseract.image_to_string(small, config='--oem 3 --psm 6')
            
            # Score: count alphanumeric chars (readable text has more)
            alpha_count = sum(1 for c in text if c.isalnum())
            # Bonus for Indonesian document keywords
            upper = text.upper()
            keyword_bonus = sum(10 for kw in ['NIK', 'NAMA', 'PROVINSI', 'ALAMAT', 'LAHIR', 
                                               'PASSPORT', 'VISA', 'PASPOR'] if kw in upper)
            score = alpha_count + keyword_bonus
            
            logger.debug(f"Rotation {angle}: score={score}, alpha={alpha_count}, keywords={keyword_bonus}")
            
            if score > best_score:
                best_score = score
                best_image = rotated
                best_angle = angle
        except Exception:
            continue
    
    if best_angle != "0":
        logger.info(f"Brute-force rotation: best angle = {best_angle} degrees (score={best_score})")
    
    return best_image


def preprocess_universal(image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Universal Preprocessing - Creates TWO versions for maximum OCR accuracy
    
    Returns:
        Tuple of (img_binary, img_gray):
        - img_binary: Adaptive threshold (good for KTP/batik backgrounds)
        - img_gray: Enhanced grayscale (good for passports/visas with clean backgrounds)
    """
    # Step 1: Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    
    # Step 2: Upscale 2x for better small text recognition
    height, width = gray.shape
    scaled = cv2.resize(gray, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)
    
    # Step 3: Denoise (mild, preserves text edges)
    denoised = cv2.fastNlMeansDenoising(scaled, None, h=10, templateWindowSize=7, searchWindowSize=21)
    
    # VERSION 1: Binary (Adaptive Threshold) - Best for KTP with batik
    img_binary = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=10
    )
    
    # VERSION 2: Enhanced Grayscale - Best for Passports/Visas
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img_gray = clahe.apply(denoised)
    
    return img_binary, img_gray


def extract_text_from_image(image_bytes: bytes, filename: str = "") -> str:
    """
    Universal OCR - Runs OCR on both preprocessed versions and combines results
    
    Args:
        image_bytes: Image file content as bytes
        filename: Original filename (for logging)
        
    Returns:
        Combined extracted text from the image
    """
    logger.info(f"Universal OCR processing: {filename}")
    
    if not TESSERACT_AVAILABLE:
        logger.error("pytesseract not available!")
        return ""
    
    try:
        # Convert bytes to OpenCV format
        pil_image = Image.open(io.BytesIO(image_bytes))
        if pil_image.mode in ('RGBA', 'LA', 'P'):
            pil_image = pil_image.convert('RGB')
        cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        
        # Step 1: Detect and crop card from photo (handles phone photos of cards on surfaces)
        cv_image = detect_and_crop_card(cv_image)
        
        # Step 2: Auto-rotate if needed (handles rotated cards)
        cv_image = auto_rotate_image(cv_image)
        
        # Get both preprocessed versions
        img_binary, img_gray = preprocess_universal(cv_image)
        
        # Tesseract configs
        config_standard = '--oem 3 --psm 6'  # Uniform text block
        
        # Run OCR on both versions
        try:
            text_binary = pytesseract.image_to_string(img_binary, config=f'{config_standard} -l eng+ind')
        except:
            text_binary = pytesseract.image_to_string(img_binary, config=config_standard)
        
        try:
            text_gray = pytesseract.image_to_string(img_gray, config=f'{config_standard} -l eng+ind')
        except:
            text_gray = pytesseract.image_to_string(img_gray, config=config_standard)
        
        # Combine results (use the longer one as base, supplement with other)
        if len(text_binary) > len(text_gray):
            combined_text = text_binary + "\n---GRAY---\n" + text_gray
        else:
            combined_text = text_gray + "\n---BINARY---\n" + text_binary
        
        # DEBUG: Print raw OCR output
        print("\n" + "="*70)
        print(f"--- RAW OCR TEXT for {filename} ---")
        print("="*70)
        print(f"[BINARY VERSION - {len(text_binary)} chars]")
        print(text_binary[:500] + "..." if len(text_binary) > 500 else text_binary)
        print("-"*70)
        print(f"[GRAY VERSION - {len(text_gray)} chars]")
        print(text_gray[:500] + "..." if len(text_gray) > 500 else text_gray)
        print("="*70 + "\n")
        
        logger.info(f"Extracted {len(combined_text)} chars from {filename}")
        
        return combined_text
        
    except Exception as e:
        logger.error(f"OCR error for {filename}: {e}", exc_info=True)
        return ""


def convert_pdf_to_images(file_content: bytes) -> List[Image.Image]:
    """Convert PDF content to list of PIL Images"""
    if not PDF_SUPPORT:
        raise ImportError("PDF support not available. Install pdf2image and poppler.")
    return convert_from_bytes(file_content, dpi=200)

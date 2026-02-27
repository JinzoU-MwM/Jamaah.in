# OCR Service Architecture

## Overview
Multi-engine OCR system for Indonesian document processing (KTP, Passport, Visa).

## OCR Engines (Priority Order)

### 1. Gemini AI Vision (Primary)
- **Best for**: Indonesian KTP with batik backgrounds, passports, low-quality images
- **Model**: `gemini-2.0-flash` (configurable)
- **Config**: `GEMINI_API_KEY` environment variable
- **Function**: `extract_text_gemini()`

### 2. Google Cloud Vision (Alternative)
- **Best for**: High-volume processing, complex layouts
- **Config**: `GCV_CREDENTIALS_PATH` environment variable
- **Function**: `extract_text_gcv()`

### 3. Tesseract (Fallback)
- **Best for**: Offline processing, cost-sensitive use cases
- **Preprocessing**: Binary, Grayscale, Enhanced (CLAHE + sharpening)
- **Function**: `_extract_text_tesseract()`

## Configuration

```bash
# Environment variables
OCR_PRIMARY_ENGINE=gemini        # gemini | google_vision | tesseract
OCR_FALLBACK_ENABLED=true        # Enable fallback chain
GEMINI_API_KEY=your_api_key      # Gemini AI API key
GEMINI_MODEL=gemini-2.0-flash    # Gemini model
GCV_CREDENTIALS_PATH=/path/to/credentials.json  # GCV credentials
```

## Key Files
- `services/ocr_service.py` - Main OCR logic
- `config.py` - Configuration settings

## Functions
- `extract_text_from_image()` - Main entry point with fallback chain
- `extract_document_data()` - Document type detection + field extraction
- `get_ocr_status()` - Check engine availability
- `preprocess_universal()` - Image preprocessing pipeline

## Document Types Supported
1. **KTP** - Indonesian ID card (NIK, name, DOB, address)
2. **Passport** - With MRZ parsing (TD3 format)
3. **Visa** - Saudi visa extraction

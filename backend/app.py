import os
import json
from typing import List
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import google.generativeai as genai
import pytesseract
from PIL import Image, ImageOps
from dotenv import load_dotenv
import pillow_heif
import io
from fastapi.concurrency import run_in_threadpool
import re

# gemini
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
pytesseract.pytesseract.tesseract_cmd = os.getenv('TESSERACT_CMD_PATH')

genai.configure(api_key=GOOGLE_API_KEY)

# Output models
class TranslationItem(BaseModel):
    lang_detected: str = Field(..., example='es', description="Language code detected for the term")
    term: str = Field(..., example='ropa vieja', description="The original slang term.")
    contextual_translation: str = Field(..., example='shredded beef stew')

class TranslationResponse(BaseModel):
    original_text: str = Field(..., example="Prueba la ropa vieja! Dale!")
    translations: List[TranslationItem]

# Helper to clean OCR text
def clean_ocr_text(text: str) -> str:
    # Replace newlines with spaces
    text = text.replace("\n", " ")
    # Remove non-printable/odd characters (optional)
    text = re.sub(r"[^\w\s.,!?¿¡:]", "", text)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()

async def get_translation_from_gemini(full_text: str) -> TranslationResponse:
    # Prompt Engineering (same as before)
    identity = """
    You are a very highly skilled and specialized cultural linguist and Miami native...
    """
    task = "### YOUR TASK: Identify slang/idioms in Miami context."
    rules = """
    ### RULES:
    1. Output ONLY valid JSON...
    """
    context = "### CONTEXT: Examples of Cuban/Haitian slang..."
    required_output = """
    ### REQUIRED JSON OUTPUT STRUCTURE: { "original_text": "...", "translations": [] }
    """
    user_request = f"""
    ### USER REQUEST:
    Analyze the following text and return JSON: "{full_text}"
    """

    system_prompt = "\n".join([identity, task, rules, context, required_output, user_request])

    model = genai.GenerativeModel(
        'gemini-1.5-flash-latest',
        generation_config={'response_mime_type': "application/json"}
    )
    
    response = model.generate_content(system_prompt)
    response_json = json.loads(response.text)
    return TranslationResponse(**response_json)

# Register HEIF opener
pillow_heif.register_heif_opener()
app = FastAPI(title='Gemini API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

# API endpoint
@app.post('/translate-image', response_model=TranslationResponse)
async def translate_image(file: UploadFile = File(...)):
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail='File is not an image.')

    image_bytes = await file.read()
    
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image = ImageOps.exif_transpose(image)
    except Exception:
        raise HTTPException(status_code=422, detail='Uploaded image file is corrupted.')

    extracted_text = await run_in_threadpool(pytesseract.image_to_string, image)
    extracted_text = clean_ocr_text(extracted_text)

    return await get_translation_from_gemini(extracted_text)

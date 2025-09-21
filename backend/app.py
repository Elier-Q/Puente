import os
import json
import re
import io
from typing import List

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import google.generativeai as genai
import pytesseract
from PIL import Image, ImageOps
import pillow_heif
from dotenv import load_dotenv

# ===========================
# ENV + MODEL CONFIG
# ===========================
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD_PATH")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(
    "gemini-1.5-flash-latest",
    generation_config={"response_mime_type": "application/json"},
)

# ===========================
# Pydantic Models
# ===========================
class TranslationItem(BaseModel):
    lang_detected: str = Field(..., example="es", description="Language code detected")
    term: str = Field(..., example="ropa vieja", description="The slang term or idiom")
    contextual_translation: str = Field(
        ..., example="shredded beef stew", description="Meaning of the slang"
    )

class TranslationResponse(BaseModel):
    original_text: str = Field(
        ..., example="Prueba la ropa vieja! Dale!", description="The extracted text"
    )
    translations: List[TranslationItem]

# ===========================
# Gemini Helper
# ===========================
async def get_translation_from_gemini(full_text: str) -> TranslationResponse:
    identity = """
    You are a highly skilled cultural linguist and Miami native.
    You specialize in slang, idioms, and cultural expressions unique to South Florida,
    including Cuban and Haitian-Creole influences.
    """

    task = """
    ### TASK:
    Identify slang, idioms, or culturally significant terms from the given text.
    """

    rules = """
    ### RULES:
    1. Output ONLY valid JSON.
    2. Always include 'original_text' as given.
    3. If no slang is detected, return "translations": [].
    4. Do not explain common Spanish/Creole unless it’s slang/cultural.
    5. Fix obvious OCR errors when possible.
    """

    context = """
    ### CONTEXT & EXAMPLES:
    Input: "Que bola acere, coge la guagua pa' la playa."
    Output:
    {
      "original_text": "Que bola acere, coge la guagua pa' la playa.",
      "translations": [
        {
          "lang_detected": "es-CU",
          "term": "Que bola",
          "contextual_translation": "A Cuban greeting similar to 'What's up?'"
        },
        {
          "lang_detected": "es-CU",
          "term": "acere",
          "contextual_translation": "A Cuban term for 'dude' or 'mate'."
        },
        {
          "lang_detected": "es-CU",
          "term": "guagua",
          "contextual_translation": "The Cuban word for 'bus'."
        }
      ]
    }

    Input: "Sak pase my bro? We're gonna parkear the car and go eat."
    Output:
    {
      "original_text": "Sak pase my bro? We're gonna parkear the car and go eat.",
      "translations": [
        {
          "lang_detected": "ht",
          "term": "Sak pase",
          "contextual_translation": "A Haitian Creole greeting meaning 'What's happening?'"
        },
        {
          "lang_detected": "en-SFL",
          "term": "parkear",
          "contextual_translation": "A Spanglish verb meaning 'to park'. Common in Miami."
        }
      ]
    }

    Input: "My grandmother's old clothes are in the attic."
    Output:
    {
      "original_text": "My grandmother's old clothes are in the attic.",
      "translations": []
    }
    """

    required_output = """
    ### REQUIRED JSON STRUCTURE:
    {
      "original_text": "The full original text",
      "translations": [
        {
          "lang_detected": "es-CU | ht | en-SFL",
          "term": "slang term",
          "contextual_translation": "easy explanation"
        }
      ]
    }
    """

    user_request = f"""
    ### USER INPUT:
    "{full_text}"
    """

    # Build prompt
    system_prompt = "\n".join(
        [identity, task, rules, context, required_output, user_request]
    )

    # Generate
    response = model.generate_content(system_prompt)
    raw_text = response.text.strip()
    print("RAW GEMINI RESPONSE:", raw_text)

    # Try parsing JSON
    try:
        response_json = json.loads(raw_text)
    except json.JSONDecodeError:
        # Extract first {...} block if extra text is around it
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if not match:
            raise ValueError("No JSON found in Gemini response")
        clean_json = match.group(0)
        response_json = json.loads(clean_json)

    print("PARSED JSON:", response_json)
    return TranslationResponse(**response_json)

# ===========================
# FastAPI App
# ===========================
pillow_heif.register_heif_opener()
app = FastAPI(title="Gemini Translation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===========================
# API Endpoint
# ===========================
@app.post("/translate-image", response_model=TranslationResponse)
async def translate_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File is not an image.")

    image_bytes = await file.read()
    print("Image uploaded!")

    try:
        image = Image.open(io.BytesIO(image_bytes))
        image = ImageOps.exif_transpose(image)
    except Exception:
        raise HTTPException(status_code=422, detail="Uploaded image is corrupted.")

    # OCR
    tesseract_config = r"--oem 3 --psm 6"
    extracted_text = pytesseract.image_to_string(image, config=tesseract_config).strip()

    if not extracted_text:
        raise HTTPException(status_code=422, detail="No text could be extracted.")

    return await get_translation_from_gemini(extracted_text)

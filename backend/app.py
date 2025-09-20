import os
import json
from typing import List
from fastapi import FastAPI , File , UploadFile
from pydantic import BaseModel , Field
import google.generativeai as genai
import pytesseract ; pytesseract.pytesseract.tesseract_cmd = r'"C:/Program Files/Tesseract-OCR/tesseract.exe"'
from PIL import Image

import io

# gemini
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

genai.configure(api_key=GOOGLE_API_KEY)

# input
class TranslationRequest(BaseModel):
    text_to_translate: List[str] = Field(
        ...,
        example=["Prueba la ropa vieja!" , "Dale!"],
        description='List of extracted strings by OCR'
    )
    
#output
class TranslationItem(BaseModel):
    
    lang_detected: str = Field(..., example='es', description="Language code detected for the term")
    
    term: str = Field(..., example='ropa vieja' , description="The original slang term.")
    
    contextual_translation: str = Field(..., example='shredded beef stew')
    
class TranslationResponse(BaseModel):
    
    original_text: str = Field(..., example="Prueba la ropa vieja! Dale!")
    
    translations: List[TranslationItem]
    
    
app = FastAPI(title='Gemini API')


async def get_translation_from_gemini(full_text) -> TranslationResponse:
    
    # identity -> task -> rules -> context -> examples -> required output
    system_prompt = f"""
    You are a specialized translation API. Your mission is to identify and explain slang, idioms, or culturally specific terms common in Miami, Florida.
    Your entire output MUST be a single, valid JSON object that matches the required schema. If no slang is found, return the JSON with an empty "translations" list.
    
    JSON SCHEMA:
    {{
      "original_text": "The full original text.",
      "translations": [
        {{ "lang_detected": "language-code", "term": "slang-term", "contextual_translation": "explanation" }}
      ]
    }}

    USER REQUEST:
    Analyze the following text and generate the JSON response:
    "{full_text}"
    """
    
    model = genai.GenerativeModel(
        'gemini-1.5-flash-latest',
        generation_config={'response_mime_type': "application/json"}
    )
    
    response = model.generate_content(system_prompt)
    response_json = json.loads(response.text)
    
    return TranslationResponse(**response_json)
    
    
    
# API endpoint
@app.post('/translate-image' , response_model=TranslationResponse)
async def translate_image(file: UploadFile = File(...)):
    
    image_bytes = await file.read()
    
    image = Image.open(io.BytesIO(image_bytes))
    extracted_text = pytesseract.image_to_string(image)
    
    return await get_translation_from_gemini(extracted_text)
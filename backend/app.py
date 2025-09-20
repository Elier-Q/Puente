import os
import json
from typing import List
from fastapi import FastAPI , File , UploadFile
from pydantic import BaseModel , Field
import google.generativeai as genai
import pytesseract
from PIL import Image , UnidentifiedImageError , ImageOps
from dotenv import load_dotenv
import pillow_heif
import io
from fastapi.concurrency import run_in_threadpool

# gemini
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
pytesseract.pytesseract.tesseract_cmd = os.getenv('TESSERACT_CMD_PATH')

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
    

async def get_translation_from_gemini(full_text) -> TranslationResponse:
    
    # Prompt Engineering
    identity = """
    You are a very highly skilled and specialized translator, who has upmost confidence in their ability.
    """
    task = """
    You have a mission to identify and explain slang, idioms, or culturally significant terms common in Miami, Florida. These terms may come from a variety of South Florida languages and cultures, such as Cuban, Haitian-Creole, and Venezuelan, as examples.
    """
    rules = """
    
    """
    context = """
    You may find many examples of Cuban slang and cultural terms. I have compiled a small list of possiblities, so that you grow to have a deeper understanding of your true mission:
        - Que bola? -> What's up?
        - Acere/Asere -> Similar to "dude" or "mate"
        - Yuma -> Foreigners, especially from the US
        - Guagua -> Bus
        - Le Ronca El Mango -> Colorful expression to say something is too much
        - Chevere -> Used to mean that something is cool
    """
    required_output = """
    {{
        "original_text": "The full original text",
        "translations": [
            {{'lang_detected': 'language-code' , 'term': 'slang-term' , 'contextual_translation': 'explanation'}}
        ]
    }}
    """
    post_identification = """
    After identifying the main culturally significant phrases, I need you to translate the full piece of text, using the slang you found and putting it into a form that many can understand post-translation.
    """
    user_request = f"""
    Analyze the following text and analyze an accurate JSON response and translation: "{full_text}"
    """
    
    # identity -> task -> rules -> context -> examples -> required JSON schema -> user request
    system_prompt = '\n'.join([identity,task,context,required_output,post_identification,user_request])
    
    model = genai.GenerativeModel(
        'gemini-1.5-flash-latest',
        generation_config={'response_mime_type': "application/json"}
    )
    
    response = model.generate_content(system_prompt)
    response_json = json.loads(response.text)
    
    return TranslationResponse(**response_json)
    

pillow_heif.register_heif_opener()
app = FastAPI(title='Gemini API')    

# API endpoint
@app.post('/translate-image' , response_model=TranslationResponse)
async def translate_image(file: UploadFile = File(...)):
    
    image_bytes = await file.read()
    
    image = Image.open(io.BytesIO(image_bytes))
    image = ImageOps.exif_transpose(image)
    
    extracted_text = await run_in_threadpool(pytesseract.image_to_string , image)
    extracted_text = extracted_text.strip()
    
    return await get_translation_from_gemini(extracted_text)
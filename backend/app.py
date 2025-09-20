import os
import json
from typing import List
from fastapi import FastAPI , File , UploadFile , HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel , Field
import google.generativeai as genai
import pytesseract
from PIL import Image , ImageOps
from dotenv import load_dotenv
import pillow_heif
import io
from fastapi.concurrency import run_in_threadpool

# gemini
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
#pytesseract.pytesseract.tesseract_cmd = os.getenv('TESSERACT_CMD_PATH')

genai.configure(api_key=GOOGLE_API_KEY)
    
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
    You are a very highly skilled and specialized cultural linguist and Miami native, who has upmost confidence in their ability. You have incredibly deep expertine in slang and idioms unique to South Florida's diverse communities, including Cuban and Haitian-Creole cultures.
    """
    task = """
    ### YOUR TASK:
    You have a mission to identify and explain slang, idioms, or culturally significant terms common in Miami, Florida to a tourist or newcomer.
    """
    rules = """
    ### RULES:
    1. Output ONLY valid JSON. Do not include any text or commentary before or after JSON object.
    2. Always include 'original_text' as given.
    3. If no slang or idioms are detected, you MUST return an empty list for the "translations". Do not explain common Spanish or Creole words unless they are in a unique, specific slang context.
    """
    context = """
    ### CONTEXT:
    You may find many examples of Cuban slang and cultural terms. I have compiled a small list of possiblities, so that you grow to have a deeper understanding of your true mission:
        - Que bola? -> What's up?
        - Acere/Asere -> Similar to "dude" or "mate"
        - Yuma -> Foreigners, especially from the US
        - Guagua -> Bus
        - Le Ronca El Mango -> Colorful expression to say something is too much
        - Chevere -> Used to mean that something is cool
        
    EXAMPLES (Demonstrate your expertise)
    **Input Text:** "Que bola acere, coge la guagua pa' la playa."
    **Output JSON:**
    {{
        "original_text": "Que bola acere, coge la guagua pa' la playa."
        "translations": [
            {{"lang_detected": "es-CU", "term": "Que bola", "contextual_translation: "A common Cuban greeting similar to 'What's up?' or 'How's it going'"}},
            {{"lang_detected": "es-CU", "term": "acere", "contextual_translation": "A friendly Cuban term for 'dude', 'friend', or 'mate'."}},
            {{"lang_detected: "es-CU", "term": "guagua", "contextual_translation": "The word for a public bus in Cuba and other Caribbean countries.}}
        ]
    }}
    **Input Text:** "Sak pase my bro? We're gonna parkear the car and go eat."
    **Output JSON:**
    {{
        "original_text": "Sak pase my bro? We're gonna parkear the car and go eat."
        "translations": [
            {{"lang_detected": "ht", "term": "Sak pase", "contextual_translation": "A standard greeting in Haitian Creole meaning 'What's happening?'"}},
            {{"lang_detected": "en-SFL", "term": "parkear", "contextual_translation": "A Spanglish verb meaning 'to park' (from the English 'park'). Common in South Florida.}}   
        ]
    }}
    **Input Text (Negative Example):** "My grandmother's old clothes are in the attic."
    **Output JSON:**
    {{
        "original_text": "My grandmother's old clothes are in the attic."
        "translations": []
    }}
    """
    required_output = """
    ### REQUIRED JSON OUTPUT STRUCTURE:
    {{
        "original_text": "The full original text",
        "translations": [
            {{'lang_detected': 'language-code (e.g., es-CU, ht, en-SFL)' , 'term': 'specific slang term or phrase' , 'contextual_translation': 'a brief, easy-to-understand explanation'}}
        ]
    }}
    """
    user_request = f"""
    ### USER REQUEST:
    Analyze the following text and analyze an accurate JSON response based on all the rules and examples provided: "{full_text}"
    """
    
    # identity -> task -> rules -> context -> examples -> required JSON schema -> user request
    system_prompt = '\n'.join([identity,task,rules,context,required_output,user_request])
    
    model = genai.GenerativeModel(
        'gemini-1.5-flash-latest',
        generation_config={'response_mime_type': "application/json"}
    )
    
    response = model.generate_content(system_prompt)
    
    response_json = json.loads(response.text)
    print(response_json)
    return TranslationResponse(**response_json)
    

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
@app.post('/translate-image' , response_model=TranslationResponse)
async def translate_image(file: UploadFile = File(...)):
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail='File is not an image.'
        )
    
    image_bytes = await file.read()
    print('Image Sent!')
    
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image = ImageOps.exif_transpose(image)
    except Exception:
        raise HTTPException(
            status_code=422,
            detail='Uploaded image file is corrupted.'
        )
    
    extracted_text = await run_in_threadpool(pytesseract.image_to_string , image)
    extracted_text = extracted_text.strip()
    
    return await get_translation_from_gemini(extracted_text)
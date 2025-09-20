import os
import json
from dotenv import load_dotenv
from typing import List
from fastapi import FastAPI , HTTPException
from pydantic import BaseModel , Field
import google.generativeai as genai

# gemini
load_dotenv()
try:
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    if not GOOGLE_API_KEY:
        raise ValueError('No API Key')
    genai.configure(api_key=GOOGLE_API_KEY)
except ValueError as e:
    exit()

# API data structure
class TranslationRequest(BaseModel):
    text_to_translate: List[str] = Field(
        ...,
        example=["Prueba la ropa vieja!" , "Dale!"],
        description='List of extracted strings by OCR'
    )
    
# output
class TranslationItem(BaseModel):
    
    lang_detected: str = Field(..., example='es', description="Language code detected for the term")
    
    term: str = Field(..., example='ropa vieja' , description="The original slang term.")
    
    contextual_translation: str = Field(..., example='shredded beef stew')
    
class TranslationResponse(BaseModel):
    
    original_text: str = Field(..., example="Prueba la ropa vieja! Dale!")
    
    translations: List[TranslationItem]
    
    
app = FastAPI(title='Transapp API')


def get_translation_from_gemini(full_text) -> TranslationResponse:
    identity = ''''''
    task = ''''''
    context = f''''''
    required_output = f''''''
    
    system_prompt = '\n'.join([identity,task,context,required_output])
    
    model = genai.GenerativeModel(
        'gemini-2.5-flash-lite',
        generation_config={'response_mime_type': "application/json"}
    )
    
    try:
        response = model.generate_content_async(system_prompt)
        response_json = json.loads(response.text)
        return TranslationResponse(**response_json)
    except Exception as e:
        print('Error')
        raise HTTPException(status_code=500)
    
    
    
# API endpoint
@app.post('/translate' , response_model=TranslationResponse)
async def translate_image_text(request: TranslationRequest):
    full_text = ' '.join(request.text_to_translate)
    
    translation_response = await get_translation_from_gemini(full_text)
    return translation_response

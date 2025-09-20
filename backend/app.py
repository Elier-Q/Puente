import os
import json
from typing import List
from fastapi import FastAPI , HTTPException
from pydantic import BaseModel , Field
import google.generativeai as genai

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
    
    response = model.generate_content(system_prompt)
    response_json = json.loads(response.text)
    
    return TranslationResponse(**response_json)
    
    
    
# API endpoint
@app.post('/translate' , response_model=TranslationResponse)
async def translate_image_text(request: TranslationRequest):
    full_text = ' '.join(request.text_to_translate)
    
    translation_response = get_translation_from_gemini(full_text)
    return translation_response

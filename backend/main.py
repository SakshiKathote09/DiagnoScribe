from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
import whisper
import json
from typing import List, Dict, Optional
import re
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Medical Documentation System", description="API for generating OASIS-E1 documentation from transcripts")

# CORS setup for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI API client
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")
client = OpenAI(api_key=openai_api_key)

# Whisper model for transcription
whisper_model = whisper.load_model("base")

# Documentation elements definition
class DocumentationElement(BaseModel):
    id: str
    name: str
    description: str
    depends_on: List[str] = []
    display_format: Dict

class TranscriptInput(BaseModel):
    transcript: str

class StructuredOutput(BaseModel):
    elements: Dict[str, Optional[Dict]]
    errors: Dict[str, Optional[str]]

# In-memory storage for elements (for simplicity)
ELEMENTS = [
    DocumentationElement(
        id="M1033",
        name="Risk for Hospitalization",
        description="Identifies patient characteristics that may indicate risk for hospitalization (OASIS-E1 M1033)",
        depends_on=[],
        display_format={"type": "list", "fields": ["risk_factors"]}
    ),
    DocumentationElement(
        id="M1800",
        name="Grooming",
        description="Ability to tend to personal hygiene needs (OASIS-E1 M1800)",
        depends_on=[],
        display_format={"type": "text", "field": "grooming_ability"}
    ),
    DocumentationElement(
        id="M1830",
        name="Bathing",
        description="Ability to bathe self (OASIS-E1 M1830)",
        depends_on=[],
        display_format={"type": "text", "field": "bathing_ability"}
    ),
    DocumentationElement(
        id="vitals",
        name="Vital Signs",
        description="Heart rate, blood pressure, respiratory rate, and blood sugar level",
        depends_on=[],
        display_format={"type": "table", "fields": ["heart_rate", "blood_pressure", "respiratory_rate", "blood_sugar"]}
    ),
    DocumentationElement(
        id="summary",
        name="Clinical Statement of Summary",
        description="High-level overview of the visit",
        depends_on=["M1033", "M1800", "M1830", "vitals"],
        display_format={"type": "text", "field": "summary"}
    )
]

def diarize_transcript(transcript: str) -> Dict[str, str]:
    # Simple rule-based diarization (clinician vs patient)
    sentences = transcript.split(". ")
    clinician = []
    patient = []
    for sentence in sentences:
        if any(keyword in sentence.lower() for keyword in ["patient says", "they report", "states"]):
            patient.append(sentence)
        else:
            clinician.append(sentence)
    return {
        "clinician": ". ".join(clinician),
        "patient": ". ".join(patient)
    }

def clean_response_content(content: str) -> str:
    # Remove markdown code fences and trim whitespace
    content = re.sub(r'^```json\n|```$', '', content, flags=re.MULTILINE)
    return content.strip()

async def process_element(transcript: str, element: DocumentationElement, previous_results: Dict) -> tuple[Optional[Dict], Optional[str]]:
    print(f"Processing element {element.name} with transcript: {transcript}")  # Debugging log
    output_format = {
        "M1033": 'A JSON object with a "risk_factors" field containing a list of strings, e.g., {"risk_factors": ["history of falls", "uncontrolled diabetes"]}',
        "M1800": 'A JSON object with a "grooming_ability" field containing a string, e.g., {"grooming_ability": "Needs assistance with grooming"}',
        "M1830": 'A JSON object with a "bathing_ability" field containing a string, e.g., {"bathing_ability": "Able to bathe independently"}',
        "vitals": 'A JSON object with fields "heart_rate" (integer), "blood_pressure" (string), "respiratory_rate" (integer), "blood_sugar" (integer), e.g., {"heart_rate": 78, "blood_pressure": "118/72", "respiratory_rate": 14, "blood_sugar": 130}',
        "summary": 'A JSON object with a "summary" field containing a string, e.g., {"summary": "Patient is stable with normal vital signs"}'
    }
    prompt = f"""
    You are a medical documentation assistant. Extract information from the following transcript relevant to {element.name} ({element.description}):
    Transcript: {transcript}

    Previous results for context: {json.dumps(previous_results, indent=2)}

    Rules:
    - Extract only information explicitly present in the transcript. Do not infer or add data not mentioned.
    - Return a valid JSON object matching the format: {output_format[element.id]}.
    - If there is insufficient information, return an empty object {{}}.
    - Output only JSON, with no markdown, code fences, or additional text.

    Examples:
    - For Risk for Hospitalization: {{"risk_factors": ["history of falls"]}} or {{}}
    - For Vital Signs: {{"heart_rate": 78, "blood_pressure": "118/72", "respiratory_rate": 14, "blood_sugar": 130}} or {{}}
    - For insufficient information: {{}}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a medical documentation assistant that outputs only valid JSON, with no markdown or code fences."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        raw_content = response.choices[0].message.content
        print(f"Raw response for {element.name}: {raw_content}")  # Debugging log
        cleaned_content = clean_response_content(raw_content)
        result = json.loads(cleaned_content)
        return result if result != {} else None, None
    except json.JSONDecodeError as e:
        error_msg = f"JSON parsing error for {element.name}: {e}, raw content: {raw_content}"
        print(error_msg)
        return None, error_msg
    except Exception as e:
        error_msg = f"Error processing element {element.name}: {e}"
        print(error_msg)
        return None, error_msg

@app.post("/transcribe", response_model=Dict)
async def transcribe_audio(file: UploadFile = File(...)):
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    audio_data = await file.read()
    with open("temp_audio.wav", "wb") as f:
        f.write(audio_data)
    
    try:
        result = whisper_model.transcribe("temp_audio.wav")
        diarized = diarize_transcript(result["text"])
        return {
            "transcript": result["text"],
            "diarization": diarized
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.post("/generate_documentation", response_model=StructuredOutput)
async def generate_documentation(input: TranscriptInput):
    diarized = diarize_transcript(input.transcript)
    results = {}
    errors = {}
    
    # Ordered execution
    for element in ELEMENTS:
        result, error = await process_element(
            transcript=diarized["clinician"] + " " + diarized["patient"],
            element=element,
            previous_results={k: v for k, v in results.items() if k in element.depends_on}
        )
        results[element.id] = result
        if error:
            errors[element.id] = error
    
    return StructuredOutput(elements=results, errors=errors)

@app.get("/elements", response_model=List[DocumentationElement])
async def get_elements():
    return ELEMENTS
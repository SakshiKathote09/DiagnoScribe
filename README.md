# DiagnoScribe Documentation System

A system to generate OASIS-E1 compliant documentation from patient-clinician transcripts, with audio transcription, structured output, diarization, ordered execution, and a dynamic UI.

## Features

- **Backend**: FastAPI with Swagger docs, handling transcript processing and documentation generation.
- **Frontend**: ReactJS with Tailwind CSS, providing a dynamic UI for audio upload, transcript editing, documentation display with robust error handling, and a "Clear" button to reset inputs and results for new runs.
- **Extensions**:
  - Audio transcription using OpenAI Whisper.
  - Structured JSON output for documentation elements (OASIS-E1 M1033, M1800, M1830, vital signs, and clinical summary).
  - Text-based diarization to separate clinician and patient/caregiver speech.
  - Ordered execution of documentation elements with dependency handling.
  - Dynamic UI rendering based on element display formats (text, list, table).
- **Containerization**: Docker and Docker Compose for consistent local deployment.
- **Security**: API keys stored in a `.env` file for secure configuration.

## Prerequisites

- Docker
- Docker Compose
- OpenAI API key (provided in assignment)

## Project Structure

```
cliniscribe/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.jsx
│   │   └── index.css
│   ├── public/
│   │   └── index.html
│   ├── package.json
│   └── tailwind.config.js
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Setup and Hosting Locally

### Using Docker

1. Ensure Docker and Docker Compose are installed.

2. Create the project directory and save the provided artifacts (`main.py`, `App.jsx`, `App.css`, `index.jsx`, `index.css`, `package.json`, `index.html`, `requirements.txt`, `Dockerfile`, `docker-compose.yml`, `.env.example`).

3. Create `backend/.env` by copying `backend/.env.example` and adding your OpenAI API key:

   ```bash
   cp backend/.env.example backend/.env
   ```

   Edit `backend/.env` to include your API key:

   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. Create `frontend/src/index.css` with:

   ```css
   @tailwind base;
   @tailwind components;
   @tailwind utilities;
   ```

5. Create `frontend/tailwind.config.js` with:

   ```javascript
   module.exports = {
     content: ["./src/**/*.{js,jsx,ts,tsx}"],
     theme: { extend: {} },
     plugins: [],
   }
   ```

6. Build and start the services:

   ```bash
   docker-compose up --build
   ```

7. Access the services:

   - Frontend: `http://localhost:3000`
   - Backend Swagger docs: `http://localhost:8000/docs`

### Manual Setup (Alternative)

#### Backend

1. Navigate to the backend directory:

   ```bash
   cd backend
   ```

2. Create a virtual environment and activate it:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` by copying `.env.example` and adding your OpenAI API key:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` to include your API key:

   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. Run the FastAPI server:

   ```bash
   uvicorn main:app --reload
‌ده

#### Frontend

1. Navigate to the frontend directory:

   ```bash
   cd frontend
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Start the React development server:

   ```bash
   npm start
   ```

## Usage

1. Open the frontend at `http://localhost:3000`.
2. Upload an audio file (e.g., WAV, MP3, M4A) for transcription or enter a transcript manually.
3. Click **"Transcribe Audio"** to process the audio file and populate the transcript textarea.
4. Click **"Generate Documentation"** to process the transcript and display OASIS-E1 documentation elements (Risk for Hospitalization, Grooming, Bathing, Vital Signs, Clinical Summary).
5. Use the **"Clear"** button to reset the transcript, audio file, documentation results, and error messages for a new run.
6. View the generated documentation, rendered dynamically as text, lists, or tables. Errors or invalid data formats are displayed in red or yellow.

## Example Use Case

To test with a patient-caregiver-clinician conversation:
- There is test temp_audio.wav provided in backend folder.
- **Audio/Transcript Input**: Use an audio file or transcript like:
  ```
  Good morning, Mrs. Johnson. How are you feeling today? I'm feeling pretty good, nurse. No dizziness or anything like that. Yeah, she's been stable, no falls or anything. I've been helping her get around. That's great to hear. Let me check your vitals. Alright, your blood pressure is 118 over 72, heart rate is 78 beats per minute, respiratory rate is 14 breaths per minute, and your blood sugar was 130 this morning before breakfast, correct? Yes, that's right. I checked it myself. I made sure she ate something light afterward. Perfect. Any shortness of breath or trouble breathing? No, nothing like that. I feel fine. She's been doing okay with her daily stuff, but I help with her bathing and grooming. Okay, so you need assistance with bathing and grooming, Mrs. Johnson? Yes, I can’t manage those on my own anymore. Got it. Any recent falls or hospitalizations we should know about? No, she hasn’t fallen, and no hospital visits since her last checkup. I’m trying to stay steady, you know. You’re doing great. I’ll note that you’re stable with no recent falls or symptoms. We’ll keep monitoring those vitals. Anything else you want to mention? No, I think that’s it. Just keep doing what you’re doing, nurse. It’s helping. Will do. I’ll finish up the paperwork and see you next week.
  ```
- **Expected Output**:
  ```json
  {
    "elements": {
      "M1033": null,
      "M1800": {"grooming_ability": "Needs assistance with grooming"},
      "M1830": {"bathing_ability": "Needs assistance with bathing"},
      "vitals": {
        "heart_rate": 78,
        "blood_pressure": "118/72",
        "respiratory_rate": 14,
        "blood_sugar": 130
      },
      "summary": {
        "summary": "Patient is stable with normal vital signs, no dizziness, shortness of breath, or recent falls. Requires assistance with bathing and grooming."
      }
    },
    "errors": {}
  }
  ```
- **UI Display**:
  - Vital Signs: Table with heart rate, blood pressure, etc.
  - Grooming: Text indicating assistance needed.
  - Bathing: Text indicating assistance needed.
  - Summary: Text summarizing patient status.
  - Risk for Hospitalization: "No data available."
- **Clearing**: Click "Clear" to reset all inputs and results for a new audio file or transcript.


## Troubleshooting

- **OpenAI API errors**: Ensure `OPENAI_API_KEY` in `backend/.env` is correct. Check Docker logs (`docker-compose logs backend`) for raw API responses if JSON parsing errors occur.
- **Incorrect data extraction**: If elements return unexpected fields (e.g., `transfer_assistance` instead of `risk_factors`), inspect the transcript and raw responses in the logs. Refine the prompt in `main.py` to be more specific.
- **Frontend rendering errors**: If the UI crashes or shows "Invalid data format," verify the backend response matches the `display_format` in `main.py`. Check browser console errors.
- **Missing `.env`**: Ensure `backend/.env` exists with `OPENAI_API_KEY`. Use `backend/.env.example` as a template.
- **Whisper issues**: Ensure `openai-whisper==20231117` is installed and FFmpeg is available in the Docker image (included in Dockerfile). Test with clear audio files (WAV, MP3, M4A).
- **Clear button issues**: If the "Clear" button doesn’t reset the UI, check the browser console for errors and verify `App.jsx` includes the `handleClear` function.
- **Docker build fails**: Verify all files are in the correct directories and `requirements.txt` includes all dependencies.
- Ensure Docker is running and ports 3000 and 8000 are free.
- Check CORS settings in `main.py` if frontend-backend communication fails.
- Clear Docker cache with `docker-compose build --no-cache` if build issues persist.

from fastapi import FastAPI, UploadFile, File
from deepgram import Deepgram
import uvicorn
import asyncio
import json
import os
import dotenv
from dotenv import load_dotenv
load_dotenv()

# Initialize FastAPI
app = FastAPI()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")  # Fetch API key

if not DEEPGRAM_API_KEY:
    raise ValueError("❌ Deepgram API Key is missing! Set the environment variable 'DEEPGRAM_API_KEY'.")

# Initialize Deepgram Client
dg_client = Deepgram(DEEPGRAM_API_KEY)

@app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Endpoint to transcribe audio using Deepgram
    """
    try:
        # Read audio file
        audio_data = await file.read()

        # Deepgram request parameters
        response = await dg_client.transcription.prerecorded(
            {
                "buffer": audio_data,
                "mimetype": file.content_type,
            },
            {"punctuate": True}
        )

        # Extract transcript
        transcript = response["results"]["channels"][0]["alternatives"][0]["transcript"]
        return {"transcript": transcript}

    except Exception as e:
        return {"error": str(e)}

# Run server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

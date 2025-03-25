from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
from .services.deepgram_service import DeepgramService
from .services.groq_service import GroqService
from .services.livekit_service import LiveKitService
from datetime import datetime

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
deepgram_service = DeepgramService()
groq_service = GroqService()
livekit_service = LiveKitService()

class InterviewConfig(BaseModel):
    cv: str
    job_description: str
    system_prompt: str

@app.post("/api/interview/create")
async def create_interview(config: InterviewConfig):
    try:
        # Generate a unique room name
        room_name = f"interview_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Store interview configuration
        interview_data = {
            "room_name": room_name,
            "cv": config.cv,
            "job_description": config.job_description,
            "system_prompt": config.system_prompt,
            "created_at": datetime.now().isoformat()
        }
        
        # Save to local file
        with open(f"interviews/{room_name}.json", "w") as f:
            json.dump(interview_data, f, indent=4)
        
        return {"room_name": room_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/livekit/token")
async def get_token(room_name: str, participant_name: str):
    token = livekit_service.create_token(room_name, participant_name)
    if not token:
        raise HTTPException(status_code=500, detail="Failed to generate token")
    return {"token": token}

@app.websocket("/ws/interview/{room_name}")
async def interview_websocket(websocket: WebSocket, room_name: str):
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "transcribe":
                transcript = await deepgram_service.transcribe_audio(
                    data["audio_data"]
                )
                await websocket.send_json({"type": "transcript", "text": transcript})
                
                # Generate next question
                question = await groq_service.generate_question(transcript)
                await websocket.send_json({"type": "question", "text": question})
            
            elif data["type"] == "evaluate":
                evaluation = await groq_service.generate_evaluation(
                    data["transcript"],
                    data["job_description"]
                )
                await websocket.send_json({"type": "evaluation", "data": evaluation})
    
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
    finally:
        await websocket.close()
from deepgram import Deepgram
import os
import asyncio

class DeepgramService:
    def __init__(self):
        self.client = Deepgram(os.getenv("DEEPGRAM_API_KEY"))

    async def transcribe_audio(self, audio_data, sample_rate=16000):
        try:
            source = {
                "buffer": audio_data,
                "mimetype": "audio/raw",
                "sample_rate": sample_rate
            }
            response = await self.client.transcription.prerecorded(
                source,
                {
                    "smart_format": True,
                    "model": "general",
                    "language": "en-US"
                }
            )
            return response["results"]["channels"][0]["alternatives"][0]["transcript"]
        except Exception as e:
            print(f"Transcription error: {str(e)}")
            return ""
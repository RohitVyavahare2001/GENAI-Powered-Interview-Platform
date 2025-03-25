from livekit import api
import os

class LiveKitService:
    def __init__(self):
        self.api_key = os.getenv("LIVEKIT_API_KEY")
        self.api_secret = os.getenv("LIVEKIT_SECRET")
        self.livekit_url = os.getenv("LIVEKIT_URL")

    def create_token(self, room_name: str, participant_name: str):
        try:
            token = api.AccessToken(
                api_key=self.api_key,
                api_secret=self.api_secret,
                identity=participant_name,
                name=participant_name
            )
            token.add_grant(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True
            )
            return token.to_jwt()
        except Exception as e:
            print(f"Token generation error: {str(e)}")
            return None
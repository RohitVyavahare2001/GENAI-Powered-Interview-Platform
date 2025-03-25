import streamlit as st
import numpy as np
import os
from dotenv import load_dotenv
import groq
import json
from datetime import datetime
import tempfile
import requests
from gtts import gTTS
import sounddevice as sd
import wave
import io
from io import BytesIO

# Load environment variables
load_dotenv()

class AIInterviewer:
    def __init__(self):
        self.transcript = []
        self.rating = None
        self.verdict = None
        self.deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
        self.groq_client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))

    def text_to_speech(self, text):
        try:
            # Use BytesIO instead of temporary file
            audio_bytes = BytesIO()
            tts = gTTS(text=text, lang='en')
            tts.write_to_fp(audio_bytes)
            audio_bytes.seek(0)
            st.audio(audio_bytes)
        except Exception as e:
            st.error(f"TTS Error: {str(e)}")

    def record_audio(self, duration=10, sample_rate=16000):
        try:
            st.write("Recording...")
            audio_data = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype=np.int16
            )
            sd.wait()
            return audio_data.tobytes()
        except Exception as e:
            st.error(f"Recording Error: {str(e)}")
            return None

    def transcribe_audio(self, audio_data):
        try:
            # Convert audio data to WAV format
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)  # 16-bit audio
                wav_file.setframerate(16000)
                wav_file.writeframes(audio_data)
            
            wav_buffer.seek(0)
            audio_bytes = wav_buffer.read()

            # Send to Deepgram API
            url = "https://api.deepgram.com/v1/listen"
            headers = {
                "Authorization": f"Token {self.deepgram_api_key}",
                "Content-Type": "audio/wav"
            }
            
            # Send request without query parameters in the URL
            response = requests.post(
                url,
                headers=headers,
                data=audio_bytes,
                json={
                    "model": "nova-2",
                    "language": "en-US",
                    "smart_format": True,
                    "punctuate": True
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['results']['channels'][0]['alternatives'][0]['transcript']
            else:
                st.error(f"Transcription failed: {response.text}")
                return ""
                
        except Exception as e:
            st.error(f"Transcription Error: {str(e)}")
            return ""

    def generate_evaluation(self, transcript, job_description):
        try:
            prompt = f"""
            Based on the following interview transcript and job description,
            provide a detailed evaluation of the candidate:
            
            Job Description: {job_description}
            Interview Transcript: {transcript}
            
            Provide evaluation in JSON format with:
            - rating (1-10)
            - verdict (detailed explanation)
            - key_strengths (list)
            - areas_for_improvement (list)
            """

            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama2-70b-4096",
                temperature=0.7,
                max_tokens=500
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            st.error(f"Evaluation Error: {str(e)}")
            return {
                "rating": 5,
                "verdict": "Unable to generate detailed evaluation",
                "key_strengths": [],
                "areas_for_improvement": []
            }

    async def generate_question(self, context):
        try:
            prompt = f"""
            You are an AI interviewer. Based on the following context,
            generate the next interview question:
            
            Previous conversation: {context}
            
            Generate a relevant follow-up question that:
            1. Builds on previous responses
            2. Evaluates technical and soft skills
            3. Maintains a natural conversation flow
            """
            
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama2-70b-4096",
                temperature=0.7,
                max_tokens=200
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"Question Generation Error: {str(e)}")
            return "Could you elaborate on your previous answer?"

def main():
    st.set_page_config(page_title="AI Interviewer", layout="wide")
    
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = 'admin'  # or 'interview'
    if 'interviewer' not in st.session_state:
        st.session_state.interviewer = AIInterviewer()
    if 'transcript' not in st.session_state:
        st.session_state.transcript = []
    if 'current_question' not in st.session_state:
        st.session_state.current_question = None

    # Admin Page
    if st.session_state.page == 'admin':
        st.title("AI Interview System - Admin Panel")
        
        with st.form("interview_setup"):
            cv = st.text_area("Candidate CV", height=200)
            job_description = st.text_area("Job Description", height=200)
            system_prompt = st.text_area(
                "System Prompt",
                value="You are conducting a technical interview for a software developer position.",
                height=100
            )
            
            if st.form_submit_button("Start Interview"):
                if cv and job_description:
                    st.session_state.cv = cv
                    st.session_state.job_description = job_description
                    st.session_state.system_prompt = system_prompt
                    st.session_state.page = 'interview'
                    st.session_state.current_question = "Hello! Thank you for joining this interview. Could you please introduce yourself?"
                    st.experimental_rerun()
                else:
                    st.error("Please fill in both CV and Job Description")

    # Interview Page
    elif st.session_state.page == 'interview':
        st.title("AI Interview")
        
        # Display current question
        if st.session_state.current_question:
            st.write("### Current Question:")
            st.write(st.session_state.current_question)
            st.session_state.interviewer.text_to_speech(st.session_state.current_question)

        # Recording controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start Recording"):
                audio_data = st.session_state.interviewer.record_audio()
                if audio_data:
                    # Transcribe audio
                    transcript = st.session_state.interviewer.transcribe_audio(audio_data)
                    if transcript:
                        st.session_state.transcript.append({
                            "question": st.session_state.current_question,
                            "answer": transcript
                        })
                        # Generate next question
                        next_question = st.session_state.interviewer.generate_question(
                            json.dumps(st.session_state.transcript)
                        )
                        st.session_state.current_question = next_question
                        st.experimental_rerun()

        with col2:
            if st.button("End Interview"):
                # Generate evaluation
                evaluation = st.session_state.interviewer.generate_evaluation(
                    st.session_state.transcript,
                    st.session_state.job_description
                )
                st.session_state.evaluation = evaluation
                st.session_state.page = 'results'
                st.experimental_rerun()

        # Display transcript
        st.write("### Interview Transcript:")
        for entry in st.session_state.transcript:
            st.write(f"**Q:** {entry['question']}")
            st.write(f"**A:** {entry['answer']}")
            st.write("---")

    # Results Page
    elif st.session_state.page == 'results':
        st.title("Interview Results")
        if 'evaluation' in st.session_state:
            st.write(f"### Rating: {st.session_state.evaluation['rating']}/10")
            st.write("### Verdict:")
            st.write(st.session_state.evaluation['verdict'])
            st.write("### Key Strengths:")
            for strength in st.session_state.evaluation['key_strengths']:
                st.write(f"- {strength}")
            st.write("### Areas for Improvement:")
            for area in st.session_state.evaluation['areas_for_improvement']:
                st.write(f"- {area}")
        
        if st.button("Start New Interview"):
            st.session_state.page = 'admin'
            st.session_state.transcript = []
            st.session_state.current_question = None
            st.experimental_rerun()

if __name__ == "__main__":
    main()
    
import groq
import os
import json

class GroqService:
    def __init__(self):
        self.client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))

    async def generate_question(self, context, personality="professional"):
        try:
            prompt = f"""
            You are an AI interviewer with a {personality} personality.
            Based on the following context, generate the next interview question:
            
            Previous conversation: {context}
            
            Generate a relevant follow-up question that:
            1. Builds on previous responses
            2. Evaluates technical and soft skills
            3. Maintains a natural conversation flow
            """

            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama2-70b-4096",
                temperature=0.7,
                max_tokens=200
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Question generation error: {str(e)}")
            return "Could you elaborate on your previous answer?"

    async def generate_evaluation(self, transcript, job_description):
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

            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama2-70b-4096",
                temperature=0.7,
                max_tokens=500
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Evaluation error: {str(e)}")
            return {
                "rating": 5,
                "verdict": "Unable to generate detailed evaluation",
                "key_strengths": [],
                "areas_for_improvement": []
            }

    async def generate_initial_question(self, cv, job_description):
        try:
            prompt = f"""
            You are an AI interviewer. Based on the following CV and job description,
            generate an appropriate opening question for the interview:
            
            CV: {cv}
            Job Description: {job_description}
            
            Generate a welcoming opening question that:
            1. Establishes rapport
            2. References the candidate's background
            3. Is open-ended and professional
            """
            
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama2-70b-4096",
                temperature=0.7,
                max_tokens=200
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Initial question generation error: {str(e)}")
            return "Could you tell me about your background and what interests you about this position?"
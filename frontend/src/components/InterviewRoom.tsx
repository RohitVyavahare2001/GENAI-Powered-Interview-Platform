import React, { useEffect, useState } from 'react';
import { Room, RoomEvent } from 'livekit-client';
import { LiveKitRoom } from '@livekit/components-react';
import { VideoConference } from './VideoConference';

interface InterviewRoomProps {
  roomName: string;
}

interface InterviewState {
  status: 'waiting' | 'in-progress' | 'completed';
  transcript: Array<{question: string; answer: string}>;
  evaluation?: {
    rating: number;
    verdict: string;
    key_strengths: string[];
    areas_for_improvement: string[];
  };
}

export const InterviewRoom: React.FC<InterviewRoomProps> = ({ roomName }) => {
  const [token, setToken] = useState<string>();
  const [ws, setWs] = useState<WebSocket>();
  const [transcript, setTranscript] = useState<string[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<string>();
  const [interviewState, setInterviewState] = useState<InterviewState>({
    status: 'waiting',
    transcript: []
  });

  useEffect(() => {
    // Get LiveKit token
    const fetchToken = async () => {
      const response = await fetch('/api/livekit/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ roomName, participantName: 'candidate' })
      });
      const data = await response.json();
      setToken(data.token);
    };

    // Connect to WebSocket
    const websocket = new WebSocket(`ws://localhost:8000/ws/interview/${roomName}`);
    setWs(websocket);

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'transcript') {
        setTranscript(prev => [...prev, data.text]);
      } else if (data.type === 'question') {
        setCurrentQuestion(data.text);
        // Use browser's TTS API to speak the question
        const speech = new SpeechSynthesisUtterance(data.text);
        window.speechSynthesis.speak(speech);
      }
    };

    fetchToken();

    return () => {
      websocket.close();
    };
  }, [roomName]);

  // Add audio recording functionality
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      const audioChunks: Blob[] = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks);
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = () => {
          const base64Audio = reader.result as string;
          ws?.send(JSON.stringify({
            type: 'transcribe',
            audio_data: base64Audio.split(',')[1]
          }));
        };
      };

      // Start recording
      mediaRecorder.start();
      
      // Stop after 30 seconds or when silence is detected
      setTimeout(() => mediaRecorder.stop(), 30000);
    } catch (error) {
      console.error('Error accessing microphone:', error);
    }
  };

  if (!token) {
    return <div>Loading...</div>;
  }

  return (
    <div className="flex h-screen">
      <div className="w-2/3 p-4">
        <LiveKitRoom
          url={process.env.REACT_APP_LIVEKIT_URL!}
          token={token}
          connect={true}
        >
          <VideoConference />
        </LiveKitRoom>
        
        <div className="mt-4">
          <button 
            onClick={startRecording}
            className="bg-blue-500 text-white px-4 py-2 rounded"
          >
            Start Speaking
          </button>
        </div>
      </div>
      
      <div className="w-1/3 p-4 bg-gray-100">
        <div className="mb-4">
          <h2 className="text-xl font-bold">Current Question:</h2>
          <p>{currentQuestion}</p>
        </div>
        
        <div className="mb-4">
          <h2 className="text-xl font-bold">Transcript:</h2>
          {transcript.map((text, index) => (
            <p key={index} className="mb-2">{text}</p>
          ))}
        </div>
      </div>
    </div>
  );
};
import React, { useState } from 'react';
import axios from 'axios';

interface ValidationErrors {
  cv?: string;
  jobDescription?: string;
  systemPrompt?: string;
}

export const AdminPanel: React.FC = () => {
  const [cv, setCV] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [interviewUrl, setInterviewUrl] = useState('');
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [isLoading, setIsLoading] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: ValidationErrors = {};
    
    if (!cv.trim()) {
      newErrors.cv = 'CV is required';
    }
    if (!jobDescription.trim()) {
      newErrors.jobDescription = 'Job description is required';
    }
    if (!systemPrompt.trim()) {
      newErrors.systemPrompt = 'System prompt is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const createInterview = async () => {
    if (!validateForm()) return;
    
    setIsLoading(true);
    try {
      const response = await axios.post('/api/interview/create', {
        cv,
        job_description: jobDescription,
        system_prompt: systemPrompt
      });
      
      const roomName = response.data.room_name;
      setInterviewUrl(`${window.location.origin}/interview/${roomName}`);
    } catch (error) {
      console.error('Failed to create interview:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Interview Configuration</h1>
      
      <div className="space-y-4">
        <div>
          <label className="block mb-2">Candidate CV</label>
          <textarea 
            className="w-full p-2 border rounded"
            value={cv}
            onChange={(e) => setCV(e.target.value)}
            rows={5}
          />
        </div>

        <div>
          <label className="block mb-2">Job Description</label>
          <textarea 
            className="w-full p-2 border rounded"
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            rows={5}
          />
        </div>

        <div>
          <label className="block mb-2">System Prompt</label>
          <textarea 
            className="w-full p-2 border rounded"
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            rows={3}
          />
        </div>

        <button 
          onClick={createInterview}
          className="bg-blue-500 text-white px-4 py-2 rounded"
        >
          Create Interview
        </button>

        {interviewUrl && (
          <div className="mt-4">
            <p>Interview URL:</p>
            <input 
              readOnly 
              value={interviewUrl} 
              className="w-full p-2 border rounded bg-gray-50"
            />
          </div>
        )}
      </div>
    </div>
  );
};
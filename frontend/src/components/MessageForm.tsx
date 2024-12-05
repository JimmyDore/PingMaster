import React, { useState, useEffect } from 'react';
import { fetchWithAuth } from '../utils/api';

interface MessageResponse {
  id: number;
  content: string;
}

export default function MessageForm() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState<MessageResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    try {
      const res = await fetchWithAuth(`${import.meta.env.PUBLIC_API_URL}/messages/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content: message }),
      });

      if (!res.ok) throw new Error('Failed to send message');
      
      const data = await res.json();
      setResponse(data);
      setMessage('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  useEffect(() => {
    fetchWithAuth(`${import.meta.env.PUBLIC_API_URL}/hello`)
        .then(res => res.json())
        .then(data => console.log('API Response:', data))
        .catch(err => console.error('API Error:', err));
  }, []);

  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-lg shadow-sm">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="message" className="block text-sm font-medium text-gray-700">
            Message
          </label>
          <input
            type="text"
            id="message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            placeholder="Enter your message"
            required
          />
        </div>

        <button
          type="submit"
          className="w-full bg-primary-600 text-white py-2 px-4 rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
        >
          Send Message
        </button>
      </form>

      {error && (
        <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-md">
          {error}
        </div>
      )}

      {response && (
        <div className="mt-4 p-3 bg-green-100 text-green-700 rounded-md">
          <p>Message created successfully!</p>
          <p>ID: {response.id}</p>
          <p>Content: {response.content}</p>
        </div>
      )}
    </div>
  );
}

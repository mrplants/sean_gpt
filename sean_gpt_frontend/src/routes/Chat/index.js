import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import authService from '../../services/authService';
import toast from 'react-hot-toast';

const ChatPage = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false); // New state for loading status

// Function to call the OpenAI completion endpoint
const getAIResponse = async (userMessage) => {
  // Format existing messages for the API
  const formattedMessages = messages.map(message => ({
    role: message.sender === 'end' ? 'user' : 'assistant',
    content: message.text,
  }));

  // Add the new user message
  formattedMessages.push({ role: 'user', content: userMessage });

  // Make the API request
  const response = await fetch('/chat/completions/openai/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authService.getToken()}`
    },
    body: JSON.stringify({
      model: "gpt-4-1106-preview",
      messages: formattedMessages,
      temperature: 1,
      max_tokens: 256,
      top_p: 1,
      frequency_penalty: 0,
      presence_penalty: 0
    }),
  });

    if (!response.ok) {
      if (response.status === 401) {
        toast.error('Please log in to continue');
        authService.logout();
        navigate('/login')
      } else {
        toast.error('Error getting AI response');
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data.choices[0].message.content;
  };

  // Handle sending a message
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (newMessage.trim()) {
      const userMessage = { text: newMessage, sender: 'end' };
      setMessages(prevMessages => [...prevMessages, userMessage]);
      setNewMessage('');
      setIsLoading(true); // Start loading

      try {
        const aiResponseText = await getAIResponse(newMessage);
        const aiResponse = { text: aiResponseText, sender: 'start' };
        setMessages(prevMessages => [...prevMessages, aiResponse]);
      } catch (error) {
        console.error('Error in handleSendMessage:', error);
        // Optionally handle the error in the UI
      } finally {
        setIsLoading(false); // Stop loading regardless of success or failure
      }
    }
  };

  return (
    <div className="grid grid-rows-[1fr_auto] h-full">
      <div className="overflow-auto p-4">
        {messages.map((message, index) => (
          <div key={index} className={`chat ${message.sender === 'end' ? 'chat-end' : 'chat-start'}`}>
            <div className="chat-bubble">{message.text}</div>
          </div>
        ))}
        {isLoading && <div className="chat-start">
          <div className="chat-bubble chat-start">
            <span className="loading loading-dots loading-md"></span>
          </div>
        </div>}
      </div>
      <div className="p-4">
        <form className="flex items-center" onSubmit={handleSendMessage} >
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type a message..."
            className="input input-bordered flex-input flex-grow mr-2"
          />
          <button type="submit" className="btn btn-primary">Send</button>
        </form >
      </div>
    </div>
  );
}

export default ChatPage;
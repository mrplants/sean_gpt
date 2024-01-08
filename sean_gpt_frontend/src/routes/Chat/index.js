import { useAuthService } from '../../services/authService';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Chat = () => {
  const [chats, setChats] = useState([]);
  const [activeChatID, setActiveChatID] = useState(null); // This is the ID of the chat that is currently being displayed
  const { isLoggedIn, user, authToken, logout } = useAuthService();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoggedIn) {
      navigate('/');
    }

    const fetchChats = async () => {
      const response = await fetch(process.env.REACT_APP_API_ENDPOINT + '/chat', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      });
      // If the response is not ok, then we should log the user out
      if (!response.ok) {
        logout();
      }

      const chatData = await response.json();
      setChats(chatData);
    };

    fetchChats();
  }, [isLoggedIn, navigate, authToken, logout]);

  useEffect(() => {
    if (chats.length > 0 && activeChatID === null) {
      setActiveChatID(chats[0].id);
    }
    // Retrieve the messages for the active chat
    const fetchMessages = async () => {
      const response = await fetch(process.env.REACT_APP_API_ENDPOINT + `/chat/message`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
          'X-Chat-Id': activeChatID,
        },
      });

      if (!response.ok) {
        logout();
      }

      const messageData = await response.json();
      console.log(messageData);
    };

    fetchMessages();
  }, [chats, activeChatID, authToken, logout]);

  const createChat = async () => {
    const response = await fetch(process.env.REACT_APP_API_ENDPOINT + '/chat', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      body: '{}',
    });

    if (!response.ok) {
      logout();
    }

    const chatData = await response.json();
    setChats([...chats, chatData]);
  }
  
  return (
    <div className="flex flex-row w-full h-full">
      <div className='relative hidden lg:flex flex-col h-full bg-base-200'>
        <div className='overflow-y-auto w-56 '>
          <ul className='menu block flex-col pt-8'>
            {
              [...chats].reverse().map((chat, index) => {
                return (
                  <li className='flex flex-row items-center my-1' onClick={() => setActiveChatID(chat.id)}>
                    <p className='grow' key={chat.id}>{chat.name === '' ? 'Chat '+(chats.length - index) : chat.name}</p>

                    {/* // TODO: Make it so that frontend does not give option for deleteing phone chat.
                    // TODO: Make it so that backend does not allow deleting phone chat.
                    // TODO: Order this by the timestamp of the latest message.*/}
                  </li>
                );
              })
            }
          </ul>
          <button className='absolute top-0 w-52 btn btn-accent btn-sm btn-outline mx-2 backdrop-blur-md' onClick={createChat}>New Chat</button>
        </div>
      </div>
      <div className="flex flex-col w-full h-full">
          <div className="flex-grow overflow-y-auto p-4">
              {/* Message Area */}
              {/* Map through messages and display them here */}
          </div>
          <div className="flex-shrink-0 flex items-center justify-between p-3">
              {/* Input Area */}
              <input
                  type="text"
                  className="w-full p-2.5 bg-gray-50 rounded-lg text-sm text-gray-900"
                  placeholder="Type a message..."
              />
              <button
                  className="btn btn-sm btn-primary ml-2"
              >
                  Send
              </button>
          </div>
      </div>
    </div>
);
}

export default Chat;

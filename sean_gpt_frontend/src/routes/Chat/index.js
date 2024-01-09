import { useAuthService } from '../../services/authService';
import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

function Message({ chat_id, chat_index }) {
  const [message, setMessage] = useState(null);
  const { authToken } = useAuthService();

  useEffect(() => {
    async function fetchMessage() {
      // Replace this with your actual fetch logic
      const response = await fetch(process.env.REACT_APP_API_ENDPOINT + `/chat/message?chat_index=${chat_index}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'X-Chat-Id': chat_id
        },
      });
      const data = await response.json();
      return data;
    }
    fetchMessage().then(setMessage);
  }, [chat_id, chat_index, authToken]);

  return (
    message ? (
    <li className={`chat ${message['role'] === 'user' ? 'chat-end' : 'chat-start'}`}>
      <div className={`chat-bubble ${message['role'] === 'assistant' ? 'chat-bubble-primary':''}`}>
        <p>{message['content']}</p>
      </div>
    </li>
    ) : (<li><span className="loading loading-spinner loading-lg"></span></li>)
  );
}

const Chat = () => {
  const [chats, setChats] = useState([]);
  const [activeChatID, setActiveChatID] = useState(null); // This is the ID of the chat that is currently being displayed
  const [activeChatMessageLen, setActiveChatMessageLen] = useState(0); // This is the number of messages in the active chat
  const { isLoggedIn, authToken, logout } = useAuthService();
  const [userMessage, setUserMessage] = useState('');
  const [pendingAssistantResponse, setPendingAssistantResponse] = useState(null); // This is used to prevent the user from sending multiple messages before the assistant responds
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
    // If an active chat ID is set:
    if (activeChatID !== null) {
      // Retrieve the number of messages in the chat
      const fetchMessages = async () => {
        const response = await fetch(process.env.REACT_APP_API_ENDPOINT + `/chat/message/len`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${authToken}`,
            'X-Chat-Id': activeChatID,
          },
        });

        if (!response.ok) {
          logout();
        }

        const messageLen = (await response.json()).len;
        setActiveChatMessageLen(messageLen);
      };
      fetchMessages();
    };

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

  const sendUserMessage = async () => {
    if (userMessage === '') {
      return;
    }

    const post_msg_response = await fetch(process.env.REACT_APP_API_ENDPOINT + '/chat/message', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
        'X-Chat-Id': activeChatID,
      },
      body: JSON.stringify({
        'role': 'user',
        'content': userMessage,
      }),
    });

    if (!post_msg_response.ok) {
      logout();
    }

    setActiveChatMessageLen(activeChatMessageLen + 1);
    setUserMessage('');

    // Send a POST request to the server
    const ai_response = await fetch(process.env.REACT_APP_API_ENDPOINT + '/chat/message/next', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'X-Chat-Id': activeChatID,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        'content': userMessage,
      }),
    });

    if (!ai_response.ok) {
      // logout();
      return;
    }
    setPendingAssistantResponse('');

    // Get the ReadableStream from the ai_response
    const reader = ai_response.body.getReader();

    // Helper function that returns a promise that resolves after a certain amount of time
    const sleep = (milliseconds) => {
      return new Promise(resolve => setTimeout(resolve, milliseconds));
    };

    // Read the stream
    while (true) {
      const { done, value } = await reader.read();

      // If the stream is done, break the loop
      if (done) {
        break;
      }

      // Convert the value to a string
      const messages = new TextDecoder().decode(value).split('data: ');
      console.log(messages)

      for (const message of messages) {
        // If the message is empty, continue to the next iteration
        if (!message) continue;

        // Add the message to the pending assistant response
        setPendingAssistantResponse(prevState => {
          // If prevState is null, return the new message
          // Otherwise, concatenate the new message to the existing state
          const stripped_message = message.substring(0,message.length-2)
          console.log(stripped_message)
          return prevState === null ? stripped_message : prevState + stripped_message;
        });

        // If the message is the last message in the array, close the reader
        if (message === messages[messages.length - 1] && pendingAssistantResponse !== null) {
          console.log('posting message: ' + pendingAssistantResponse);
          reader.cancel();
          const post_msg_response = await fetch(process.env.REACT_APP_API_ENDPOINT + '/chat/message', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${authToken}`,
              'Content-Type': 'application/json',
              'X-Chat-Id': activeChatID,
            },
            body: JSON.stringify({
              'role': 'assistant',
              'content': pendingAssistantResponse,
            }),
          });
      
          if (!post_msg_response.ok) {
            logout();
          }
          setPendingAssistantResponse(null);
          setActiveChatMessageLen(activeChatMessageLen + 1);
        }
      }
    }
  };

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }
  
  useEffect(scrollToBottom, [activeChatMessageLen, pendingAssistantResponse]);
  
  
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
            <ul className='flex flex flex-col-reverse'>
            <div ref={messagesEndRef} />
            {
                pendingAssistantResponse ? (
                  <li className="chat chat-start">
                    <div className="chat-bubble chat-bubble-primary">
                      <p>{pendingAssistantResponse}<span className="loading loading-dots loading-xs ml-1"></span></p>
                    </div>
                  </li>
                ) : null
              }
              {
                Array.from({ length: activeChatMessageLen }).reverse().map((_, index) => (
                  <Message key={activeChatMessageLen-index} chat_id={activeChatID} chat_index={activeChatMessageLen-index} />
                ))
              }
            </ul>
          </div>
          <div className="flex-shrink-0 flex items-center justify-between p-3">
              {/* Input Area */}
              <input
                  type="text"
                  className="w-full p-2.5 bg-gray-50 rounded-lg text-sm text-gray-900"
                  placeholder="Type a message..."
                  value={userMessage}
                  onChange={(e) => setUserMessage(e.target.value)}
              />
              <button
                  className="btn btn-sm btn-primary ml-2"
                  onClick={sendUserMessage}
              >
                  Send
              </button>
          </div>
      </div>
    </div>
);
}

export default Chat;

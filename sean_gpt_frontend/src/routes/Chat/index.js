import { useAuthService } from '../../services/authService';
import { useEffect, useState, useRef } from 'react';
import ChatMessage from '../../components/ChatMessage';
import { useChatService } from '../../services/chatService';

const Chat = () => {
  const { user } = useAuthService();
  const [userMessage, setUserMessage] = useState('');
  const { chats, activeChat, activeChatMessages, assistantResponse, setActiveChat, createChat, postMessage, generateResponse, deleteActiveChat, renameActiveChat } = useChatService();
  const [showMobileChats, setShowMobileChats] = useState(false);
  const [isRenamingChat, setIsRenamingChat] = useState(false);
  const [renameActiveChatName, setRenameActiveChatName] = useState('');

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }
  
  useEffect(scrollToBottom, [ activeChatMessages, assistantResponse ]);
  
  const messageSubmit = async (e) => {
    e.preventDefault();
    if (userMessage === '' || assistantResponse !== null || activeChat === null || activeChat.id === user.twilio_chat_id) {
      return;
    }
    // Start generating an assistant response
    generateResponse([...activeChatMessages, { content: userMessage, role: 'user' }]);
    // Send the message to the backend
    await postMessage('user', userMessage)
    
    // Clear the user message
    setUserMessage('');
  };

  const renameFormSubmit = async (e) => {
    e.preventDefault();
    renameActiveChat(renameActiveChatName); 
    setRenameActiveChatName('');
    setIsRenamingChat(false);
  };
  
  return (
    <div className="flex flex-row w-full h-full">
      <div className='relative hidden lg:flex flex-col h-full bg-base-200'>
        <div className='overflow-y-auto w-56 '>
          <ul className='menu block flex-col pt-8'>
            {
              chats.map((chat, index) => {
                return (
                  <li className='flex flex-row items-center my-1' onClick={() => setActiveChat(chat)}>
                    <p className='grow' key={chat.id}>{chat.name === '' ? 'Chat '+(chats.length - index) : chat.name}</p>
                  </li>
                );
              })
            }
          </ul>
          <button className='absolute top-0 w-52 btn btn-accent btn-sm btn-outline mx-2 backdrop-blur-md' onClick={() => createChat() }>New Chat</button>
        </div>
      </div>
      <div className="flex flex-col w-full h-full">
        {( activeChat === null ? (
          <div className="flex-grow flex flex-col items-center justify-center">
            <h1 className="text-3xl font-bold">Welcome to SeanGPT!</h1>
            <p className="text-xl">Select a chat to get started.</p>
          </div>
        ) : (
          <>
          <div className="flex-grow overflow-y-auto p-4">
            {/* Message Area */}
            <ul className='flex flex-col'>
              {
                activeChatMessages.sort((a, b) => a.chat_index - b.chat_index).map((chatMessage, index) => (
                  <ChatMessage key={index} message={chatMessage} />
                ))
              }
              {
                assistantResponse !== null? (
                  <ChatMessage key={-1} message={{role:'assistant', content:assistantResponse}} pending />
                ) : null
              }
              <div ref={messagesEndRef} />
            </ul>
          </div>
          <form className="flex-shrink-0 flex items-center justify-between p-3" onSubmit={ messageSubmit }>
              {/* Input Area */}
              <input
                  disabled = {assistantResponse !== null || activeChat == null || activeChat.id === user.twilio_chat_id}
                  type="text"
                  className="w-full p-2.5 bg-gray-50 rounded-lg text-sm text-gray-900 input input-bordered"
                  placeholder="Type a message..."
                  value={userMessage}
                  onChange={(e) => setUserMessage(e.target.value)}
              />
              <button
                  type='submit'
                  className={`btn btn-sm btn-primary ml-2 ${assistantResponse !== null || activeChat === null || activeChat.id === user.twilio_chat_id ? 'btn-disabled' : ''}`}>
                  Send
              </button>
          </form>
          </>
        ))}
      <div className="absolute flex flex-row right-0 items-center">
        <button className={`btn btn-sm btn-outline mt-2 mr-3 backdrop-blur-md z-50 ${activeChat === null || user.twilio_chat_id === activeChat.id ? 'hidden' : ''}`} onClick={() => setIsRenamingChat(true)}>Rename Chat</button>
        <button className={`btn btn-error btn-sm btn-outline mt-2 mr-3 backdrop-blur-md z-50 ${activeChat === null || user.twilio_chat_id === activeChat.id ? 'hidden' : ''}`} onClick={() => deleteActiveChat()}>Delete Chat</button>
        {/* This modal is the chat renaming dialog */}
        <dialog className={`modal modal-bottom sm:modal-middle ${isRenamingChat ? 'modal-open': ''}`}>
          <div className="modal-box">
            <form onSubmit={renameFormSubmit}>
              <div className="flex flex-col items-center">
                <h1 className="text-2xl font-bold">Rename{activeChat === null ? '' : ` '${activeChat.name}'`}</h1>
                <div className="form-control">
                  <input
                    type="text"
                    placeholder="New Chat Name"
                    className="input input-bordered mt-3"
                    value={renameActiveChatName}
                    onChange={(e) => setRenameActiveChatName(e.target.value)} />
                </div>
                <div className="form-control">
                  <button type='submit' className="btn btn-primary btn-md mt-3" onClick={() => setIsRenamingChat(false)}>Submit</button>
                </div>
              </div>
            </form>
          </div>
          <form method="dialog" className="modal-backdrop">
            <button onClick={() => setIsRenamingChat(false)}>close</button>
          </form>
        </dialog>
      </div>
      <div className="absolute lg:hidden flex flex-col inset-x-0 items-center">
        <button className='btn btn-accent btn-sm btn-outline mt-2 backdrop-blur-md' onClick={() => setShowMobileChats(!showMobileChats)}>Chats</button>
        <div className={`relative w-56 h-64 rounded-box ${showMobileChats ? '' : 'hidden'}`} >
          <div className="h-full overflow-y-auto rounded-box">
            <ul className='menu bg-base-200 w-56 rounded-box pt-10'>
              {
                chats.map((chat, index) => {
                  return (
                    <li className='flex flex-row items-center my-1' onClick={() => setActiveChat(chat) || setShowMobileChats(false)}>
                      <p className='grow' key={chat.id}>{chat.name === '' ? 'Chat '+(chats.length - index) : chat.name}</p>
                    </li>
                  );
                }
                )
              }
            </ul>
          </div>
          <button className='absolute top-2 w-52 btn btn-accent btn-sm btn-outline mx-2 backdrop-blur-md' onClick={() => createChat() }>New Chat</button>
        </div>
      </div>
      </div>
    </div>
);
}

export default Chat;

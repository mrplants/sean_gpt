import { createContext, useContext, useEffect, useState, useReducer } from 'react';
import { useAuthService } from './authService';
import toast from 'react-hot-toast';

const happyWords = [
    'Puppy',       // Puppies often bring joy to people.
    'Kitten',      // Similarly, kittens can be very amusing and cute.
    'Bunny',       // Bunnies are associated with happiness and springtime.
    'Butterfly',   // Butterflies symbolize beauty and transformation.
    'Sunshine',    // Associated with brightness and positivity.
    'Rainbow',     // Often seen as a symbol of hope and joy.
    'Dolphin',     // Dolphins are known for their playful nature.
    'Paradise',    // Represents an ideal or blissful state.
    'Giggles',     // Laughter is universally associated with happiness.
    'Frolic',      // To play or move about cheerfully.
    'Chirp',       // The cheerful sound of a small bird or insect.
    'Snuggle',     // Associated with comfort and affection.
    'Twinkle',     // Sparkle or shine with a light that changes constantly.
    'Whiskers',    // A feature on animals that can evoke affection.
    'Fluffy',      // Soft and light; can describe cute animals.
    'Honeybee',    // Bees produce honey and are often seen in positive light.
    'Lambkin',     // A term of endearment for a young lamb.
    'Peachy',      // Excellent or wonderful.
    'Meadow',      // A field of grass that invokes feelings of tranquility.
    'Carousel',    // A merry-go-round; associated with fun and playfulness.
  ];
  
  // Function to generate a random happy word
  function getRandomHappyWord() {
    const index = Math.floor(Math.random() * happyWords.length);
    return happyWords[index];
  }
  
// Create a Context
const ChatContext = createContext(null);

/**
 * Custom hook to use the chat context.
 * @returns The chat context.
 */
export function useChatService() {
  return useContext(ChatContext);
}

const activeChatMessagesReducer = (state, action) => {
    switch (action.type) {
        case 'set':
            return action.messages;
        case 'add':
            return [...state, action.message];
        default:
            return state;
    }
}

const assistantResponseReducer = (state, action) => {
    switch (action.type) {
        case 'init':
            return null;
        case 'append':
            if (state === null) {
                return action.msg_delta;
            } else {
                return state + action.msg_delta;
            }
        default:
            return state;
    }
}

const GeneratorStatus = {
    IDLE: 'idle',
    GENERATING: 'generating',
    DONE: 'done',
}

/**
 * Provider component for authentication context.
 * @param {object} props - The props object.
 * @param {React.ReactNode} props.children - The children nodes.
 */
export function ChatProvider({ children }) {
    const { authToken } = useAuthService();
    const [chats, setChats] = useState([]);
    const [activeChat, setActiveChat] = useState(null);
    const [generatingState, setGeneratingState] = useState(GeneratorStatus.IDLE);
    const [activeChatMessages, dispatchActiveChatMessage] = useReducer(activeChatMessagesReducer, []);
    const [assistantResponse, dispatchAssistantResponse] = useReducer(assistantResponseReducer, null);
    const [backendWebsocket, setBackendWebsocket] = useState(null);

    useEffect(() => {
        if (generatingState === GeneratorStatus.DONE && assistantResponse !== null) {
            // The generator is done and the message should be posted
            postMessage('assistant', assistantResponse);
            // Reset the assistant response
            dispatchAssistantResponse({ type: 'init' });
            setGeneratingState(GeneratorStatus.IDLE);
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [generatingState]);

    // Effect for fetching chats when page is loaded
    useEffect(() => {
        if (!authToken) {
            return;
        }
        // Fetch all the chats from the /chat endpoint
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
                toast.error('Error fetching chats');
                console.log(response);
                return
            }

            const chatData = await response.json();
            setChats(chatData);
        };

        fetchChats();
    }, [authToken]);

    // Effect for fetching messages when active chat is changed
    useEffect(() => {
        dispatchActiveChatMessage({ type: 'set', messages: [] });
        
        // if the active chat is null, return
        if (activeChat === null || authToken === null) {
            return;
        }
        
        fetch(process.env.REACT_APP_API_ENDPOINT + `/chat/message/len`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'X-Chat-Id': activeChat.id,
            },
        }).then(async (response) => {
            if (!response.ok) {
                toast.error('Error fetching messages');
                console.log(response);
                return;
            }
            const messageLen = (await response.json()).len;
            for (let i = 0; i < messageLen; i++) {
                fetch(process.env.REACT_APP_API_ENDPOINT + `/chat/message?chat_index=${messageLen-i-1}`, {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${authToken}`,
                        'X-Chat-Id': activeChat.id, 
                    },
                }).then(async (messageResponse) => {
                    if (!messageResponse.ok) {
                        toast.error('Error fetching messages');
                        console.log(messageResponse);
                        return;
                    }
                
                    const message = await messageResponse.json();
                    dispatchActiveChatMessage({ type: 'add', message });
                });
            }
        });
    }, [activeChat, authToken ]);

    const createChat = async () => {
        const name = getRandomHappyWord() + ' Chat';
        const response = await fetch(process.env.REACT_APP_API_ENDPOINT + '/chat', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json',
            },
            body: name ? JSON.stringify({ name }) : '{}',
        });
      
        if (!response.ok) {
            toast.error('Error creating chat');
            console.log(response);
            return;
        }
      
        const chatData = await response.json();
        setChats([...chats, chatData]);
    };

    const postMessage = async (role, content) => {
        const response = await fetch(process.env.REACT_APP_API_ENDPOINT + '/chat/message', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json',
                'X-Chat-Id': activeChat.id,
            },
            body: JSON.stringify({
                role,
                content,
            }),
        });

        if (!response.ok) {
            toast.error('Error posting message');
            console.log(response);
            return;
        }
        const response_message = await response.json();
        dispatchActiveChatMessage({ type: 'add', message: response_message });
    };

    const generateResponse = async (messages) => {
        if (generatingState !== GeneratorStatus.IDLE) {
            return;
        }
        dispatchAssistantResponse({ type: 'append', msg_delta: '' });

        // Create the list of messages to send to the backend
        // First, order the messages by the key 'chat_index', then map them to the correct format
        const conversation = messages.sort((a, b) => a.chat_index - b.chat_index).map((message) => {
            return {
                role: message.role,
                content: message.content,
            };
        });
        
        // POST /chat/generate with the conversation to get a stream token
        const stream_token_response = await fetch(process.env.REACT_APP_API_ENDPOINT + '/generate/chat/token', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json',
            }
        });
        if (!stream_token_response.ok) {
            toast.error('Error generating response');
            console.log(stream_token_response);
            return;
        }
        const ws_token = (await stream_token_response.json())['token'];

        // Create the websocket connection
        var ws = new WebSocket(process.env.REACT_APP_API_ENDPOINT.replace(/^http/, 'ws') + '/generate/chat/ws?token=' + ws_token);
        setBackendWebsocket(ws);

        ws.onopen = () => {
            // Send the conversation to the websocket
            ws.send(JSON.stringify({
                action: 'chat_completion',
                payload: {
                    conversation: conversation
                }
            }));
            setGeneratingState(GeneratorStatus.GENERATING);
        };
        ws.onmessage = (event) => {
            // When the websocket sends a message, append it to the pending assistant response
            dispatchAssistantResponse({ type: 'append', msg_delta: event.data });
        };
        ws.onclose = () => {
            // When the websocket closes, post the message to the backend
            // Wait a second so that all the connectiosn are rendered
            const postAndReset = async () => {
                await new Promise(resolve => setTimeout(resolve, 1000)); // Wait for 1 second
                setGeneratingState(GeneratorStatus.DONE);
            };
            postAndReset();
            setBackendWebsocket(null);
        };
        ws.onerror = (error) => {
            toast.error('Error generating response');
            console.log(error);
        }
    };

    const deleteActiveChat = async () => {
        const delete_response = await fetch(process.env.REACT_APP_API_ENDPOINT + '/chat', {
            method: 'DELETE',
            headers: {
                "Authorization": `Bearer ${authToken}`,
                "X-Chat-Id": activeChat.id,
            },
        });

        if (!delete_response.ok) {
            toast.error('Error deleting chat');
            console.log(delete_response);
            return;
        }

        setChats(chats.filter((chat) => chat.id !== activeChat.id));
        toast.success( activeChat.name === '' ? 'Chat deleted' : `Deleted ${activeChat.name}`);
        setActiveChat(null);
    };

    const renameActiveChat = async (name) => {
        const rename_response = await fetch(process.env.REACT_APP_API_ENDPOINT + '/chat', {
            method: 'PUT',
            headers: {
                "Authorization": `Bearer ${authToken}`,
                "X-Chat-Id": activeChat.id,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ name:name }),
        });

        if (!rename_response.ok) {
            toast.error('Error renaming chat');
            console.log(rename_response);
            return;
        }

        // Retrieve the updated chat
        const response = await fetch(process.env.REACT_APP_API_ENDPOINT + '/chat?id=' + activeChat.id, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json',
            },
        });

        // If the response is not ok
        if (!response.ok) {
            toast.error('Error renaming chat');
            console.log(response);
            return
        }

        const chatData = (await response.json())[0];
        setChats(chats.map((chat) => chat.id === chatData.id ? chatData : chat));
        setActiveChat(chatData);
        toast.success(`Renamed to '${name}'`);
    }

    return (
        <ChatContext.Provider value={{ chats, activeChat, activeChatMessages, assistantResponse, setActiveChat, createChat, postMessage, generateResponse, deleteActiveChat, renameActiveChat, backendWebsocket }}>
        {children}
        </ChatContext.Provider>
    );
}

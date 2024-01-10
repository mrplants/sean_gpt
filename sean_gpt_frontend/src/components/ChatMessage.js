import Markdown from 'react-markdown'

function ChatMessage({ message, pending }) {
    
    return (
        message ? (
        <li className={`chat ${message['role'] === 'user' ? 'chat-end' : 'chat-start'}`}>
            <div className={`flex flex-col items-center chat-bubble ${message['role'] === 'assistant' ? 'chat-bubble-primary':''}`}>
            <Markdown className="text-wrap">{message['content']}</Markdown>
            {pending ? <span className="loading loading-dots loading-md"></span> : null}
            </div>
        </li>
        ) : (<li><span className="loading loading-spinner loading-lg"></span></li>)
    );
}
  
export default ChatMessage;
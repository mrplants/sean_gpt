import Markdown from 'react-markdown'
import {Prism as SyntaxHighlighter} from 'react-syntax-highlighter'
import {vs, vscDarkPlus} from 'react-syntax-highlighter/dist/esm/styles/prism'

function ChatMessage({ message, pending }) {
    const isDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const style = isDarkMode ? vscDarkPlus : vs;
    return (
        message ? (
        <li className={`chat ${message['role'] === 'user' ? 'chat-end' : 'chat-start'}`}>
            <div className={`flex flex-col items-center chat-bubble ${message['role'] === 'assistant' ? 'chat-bubble-primary':''}`}>
                {
                    message['role'] === 'user' ? (
                    <p className="whitespace-break-spaces px-4 break-word">{message['content']}</p>
                    ) : (
                    <Markdown className="whitespace-break-spaces min-w-0" components={{
                        code(props) {
                            const {children, className, node, ...rest} = props
                            const match = /language-(\w+)/.exec(className || '')
                            return match ? (
                            <SyntaxHighlighter
                                {...rest}
                                PreTag="div"
                                children={String(children).replace(/\n$/, '')}
                                language={match[1]}
                                style={style}
                                wrapLongLines={true}
                                wrapLines={true}
                                lineProps={{style: {wordBreak: 'break-all', whiteSpace: 'pre-wrap'}}}
                            />
                            ) : (
                            <code {...rest} className={className}>
                                {children}
                            </code>
                            )
                        }
                    }}>{message['content']}</Markdown>
                    )
                }
            {pending ? <span className="loading loading-dots loading-md"></span> : null}
            </div>
        </li>
        ) : (<li><span className="loading loading-spinner loading-lg"></span></li>)
    );
}
  
export default ChatMessage;
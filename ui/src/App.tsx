import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport, UIMessage } from "ai";
import { useState, useEffect, useRef } from "react";
import "./App.css";

function App() {
  const [input, setInput] = useState("");
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const apiUrl = import.meta.env.VITE_API_BASE_URL
    ? `${import.meta.env.VITE_API_BASE_URL}/agent/stream`
    : "http://localhost:5001/agent/stream";

  const { messages, sendMessage, status, error } = useChat({
    transport: new DefaultChatTransport({
      api: apiUrl,
    }),
  });

  const isLoading = status === "submitted" || status === "streaming";

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`;
    }
  }, [input]);

  const handleSubmit = (e?: React.FormEvent<HTMLFormElement>) => {
    e?.preventDefault();

    if (!input.trim() || isLoading) return;

    sendMessage({ text: input });
    setInput("");
    setAttachedFiles([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Enter to send, Shift+Enter for newline
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setAttachedFiles((prev) => [...prev, ...files]);
  };

  const removeFile = (index: number) => {
    setAttachedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const renderMessageContent = (message: UIMessage) => {
    return (
      <>
        {message.parts.map((part, idx) => {
          if (part.type === "text") {
            return (
              <div key={`text-${idx}`} className="message-text">
                {part.text}
              </div>
            );
          } else if (part.type.startsWith("tool-")) {
            return (
              <details key={`tool-${idx}`} className="tool-call">
                <summary>
                  {part.type}
                </summary>
                <pre className="tool-json">{JSON.stringify(part, null, 2)}</pre>
              </details>
            );
          } else if(part.type === 'step-start'){
            return <hr />
          }
        })}
      </>
    );
  };

  return (
    <div className="chat-container">
      <header className="chat-header">
        <h1>🤖 LLM Agent Demo</h1>
        <p>Powered by LangChain + Vercel AI SDK</p>
      </header>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">💬</div>
            <h2>Start a conversation</h2>
            <p>Type a message below to get started</p>
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} className={`message-wrapper ${message.role}`}>
            <div className="message-avatar">
              {message.role === "user" ? "👤" : "🤖"}
            </div>
            <div className="message-bubble">
              <div className="message-header">
                {message.role === "user" ? "You" : "AI Assistant"}
              </div>
              <div className="message-content">
                {renderMessageContent(message)}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message-wrapper assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-bubble">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="error-banner">
            <span className="error-icon">⚠️</span>
            <span>{error.message}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        {attachedFiles.length > 0 && (
          <div className="attached-files">
            {attachedFiles.map((file, index) => (
              <div key={index} className="file-chip">
                <span>📎 {file.name}</span>
                <button
                  type="button"
                  onClick={() => removeFile(index)}
                  className="file-remove"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        <form onSubmit={handleSubmit} className="chat-input-form">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleFileSelect}
            style={{ display: "none" }}
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="attach-button"
            title="Attach file"
            disabled={isLoading}
          >
            📎
          </button>

          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message... (Enter to send, Shift+Enter for newline)"
            disabled={isLoading}
            className="chat-input"
            rows={1}
          />

          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="send-button"
            title="Send message"
          >
            {isLoading ? "⏳" : "📤"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;

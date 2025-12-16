import { useChat } from '@ai-sdk/react';
import { DefaultChatTransport } from 'ai';
import { useState } from 'react';
import './App.css';

function App() {
  const [input, setInput] = useState('');
  
  const apiUrl = import.meta.env.VITE_API_BASE_URL 
    ? `${import.meta.env.VITE_API_BASE_URL}/agent/stream`
    : 'http://localhost:8000/agent/stream';
  
  const { messages, sendMessage, status, error } = useChat({
    transport: new DefaultChatTransport({
      api: apiUrl,
    }),
  });
  
  const isLoading = status === 'submitted' || status === 'streaming';

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    if (!input.trim() || isLoading) return;

    sendMessage({ text: input });
    setInput('');
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>LLM Agent Demo</h1>
        <p>Submit a prompt to the AI agent (with streaming)</p>
      </header>

      <main className="App-main">
        <form onSubmit={handleSubmit} className="prompt-form">
          <div className="form-group">
            <label htmlFor="prompt">Your Prompt:</label>
            <textarea
              id="prompt"
              name="prompt"
              placeholder="Enter your question or prompt here..."
              rows={5}
              disabled={isLoading}
              className="prompt-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
          </div>

          <button 
            type="submit" 
            disabled={isLoading || !input.trim()}
            className="submit-button"
          >
            {isLoading ? 'Processing...' : 'Submit'}
          </button>
        </form>

        {isLoading && (
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Streaming response...</p>
          </div>
        )}

        {error && (
          <div className="error-message">
            <h3>Error</h3>
            <p>{error.message}</p>
          </div>
        )}

        {messages.length > 0 && (
          <div className="messages-container">
            <h3>Conversation:</h3>
            {messages.map((message) => {
              // Extract text from message parts
              const content = message.parts
                .filter((part: any) => part.type === 'text')
                .map((part: any) => part.text)
                .join('');
              
              return (
                <div 
                  key={message.id} 
                  className={`message ${message.role}`}
                >
                  <strong>{message.role === 'user' ? 'You' : 'AI'}:</strong>
                  <div className="message-content">
                    {content}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>

      <footer className="App-footer">
        <p>Powered by FastAPI + LangChain + React + Vercel AI SDK</p>
      </footer>
    </div>
  );
}

export default App;

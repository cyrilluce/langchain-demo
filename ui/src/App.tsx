import { useState } from 'react';
import { submitPrompt, ApiError, TimeoutError } from './services/api';
import type { LoadingState } from './types';
import './App.css';

function App() {
  const [prompt, setPrompt] = useState('');
  const [answer, setAnswer] = useState('');
  const [loadingState, setLoadingState] = useState<LoadingState>('idle');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!prompt.trim()) {
      setError('Please enter a prompt');
      return;
    }

    setLoadingState('loading');
    setError(null);
    setAnswer('');

    try {
      const response = await submitPrompt(prompt);
      setAnswer(response);
      setLoadingState('success');
    } catch (err) {
      if (err instanceof TimeoutError) {
        setError('Request timed out after 6 minutes. Please try a simpler prompt or check your connection.');
        setLoadingState('timeout');
      } else if (err instanceof ApiError) {
        if (err.status === 503) {
          setError(`LLM service unavailable: ${err.message}`);
        } else {
          setError(err.message);
        }
        setLoadingState('error');
      } else {
        setError('An unexpected error occurred');
        setLoadingState('error');
      }
    }
  };

  const isLoading = loadingState === 'loading';

  return (
    <div className="App">
      <header className="App-header">
        <h1>LLM Agent Demo</h1>
        <p>Submit a prompt to the AI agent</p>
      </header>

      <main className="App-main">
        <form onSubmit={handleSubmit} className="prompt-form">
          <div className="form-group">
            <label htmlFor="prompt">Your Prompt:</label>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter your question or prompt here..."
              rows={5}
              disabled={isLoading}
              className="prompt-input"
            />
          </div>

          <button 
            type="submit" 
            disabled={isLoading || !prompt.trim()}
            className="submit-button"
          >
            {isLoading ? 'Processing...' : 'Submit'}
          </button>
        </form>

        {isLoading && (
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Waiting for response (this may take up to 6 minutes)...</p>
          </div>
        )}

        {error && (
          <div className="error-message">
            <h3>Error</h3>
            <p>{error}</p>
          </div>
        )}

        {answer && loadingState === 'success' && (
          <div className="answer-display">
            <h3>Response:</h3>
            <div className="answer-content">
              {answer}
            </div>
          </div>
        )}
      </main>

      <footer className="App-footer">
        <p>Powered by FastAPI + LangChain + React</p>
      </footer>
    </div>
  );
}

export default App;

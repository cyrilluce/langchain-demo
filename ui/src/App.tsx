import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./App.css";

function App() {
  const navigate = useNavigate();

  useEffect(() => {
    // Generate a new thread ID or use a default one
    const threadId = `thread-${Date.now()}`;
    navigate(`/chat/${threadId}`, { replace: true });
  }, [navigate]);

  return (
    <div className="chat-container">
      <div className="loading-state">
        <h2>Starting new conversation...</h2>
      </div>
    </div>
  );
}

export default App;


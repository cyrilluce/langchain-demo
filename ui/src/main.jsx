import React, {useState} from 'react'
import {createRoot} from 'react-dom/client'

function App(){
  const [prompt, setPrompt] = useState('Hello')
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(){
    setLoading(true)
    try{
      const res = await fetch('http://localhost:8000/agent', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({prompt})
      })
      const data = await res.json()
      setAnswer(data.answer ?? 'no-answer')
    }catch(e){
      setAnswer('error: ' + String(e))
    }finally{
      setLoading(false)
    }
  }

  return (
    <div style={{fontFamily:'Arial, sans-serif', padding:20}}>
      <h1>LLM Agent UI (demo)</h1>
      <textarea value={prompt} onChange={e=>setPrompt(e.target.value)} rows={4} cols={60} />
      <div style={{marginTop:10}}>
        <button onClick={submit} disabled={loading}>Send</button>
      </div>
      <div style={{marginTop:20}}>
        <strong>Answer:</strong>
        <pre>{answer}</pre>
      </div>
    </div>
  )
}

createRoot(document.getElementById('root')).render(React.createElement(App))

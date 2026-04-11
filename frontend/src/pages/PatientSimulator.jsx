import React, { useState, useEffect, useRef } from 'react';
import './PatientSimulator.css';

export default function PatientSimulator() {
  const [callActive, setCallActive] = useState(false);
  const [chatLog, setChatLog] = useState([]);
  const [systemState, setSystemState] = useState({ keywords: [], risk: 'NORMAL', action: 'Monitoring' });
  const [isTyping, setIsTyping] = useState(false);
  
  // Speech Recognition States
  const [isListening, setIsListening] = useState(false);
  const [recognition, setRecognition] = useState(null);
  const [liveTranscript, setLiveTranscript] = useState('');
  
  const transcriptRef = useRef('');
  const chatEndRef = useRef(null);

  useEffect(() => {
    // Initialize Web Speech API
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const rec = new SpeechRecognition();
      rec.continuous = true;
      rec.interimResults = true;
      rec.lang = 'en-IN'; // Recognizing Indian English by default

      rec.onstart = () => {
        setIsListening(true);
        setLiveTranscript('');
        transcriptRef.current = '';
      };
      
      rec.onresult = (event) => {
        let interimTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          interimTranscript += event.results[i][0].transcript;
        }
        transcriptRef.current = interimTranscript;
        setLiveTranscript(interimTranscript);
      };

      rec.onerror = (event) => {
        console.error('Speech recognition error', event.error);
        if (event.error === 'not-allowed') {
          setIsListening(false);
        }
      };

      rec.onend = () => {
        setIsListening(false);
      };
      
      setRecognition(rec);
    } else {
      console.warn("Speech Recognition API not supported in this browser.");
    }
  }, []);

  const speakText = (text) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel(); // Stop prior speech
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'en-IN';
      utterance.rate = 0.95; // Slightly slower for an empathetic tone
      utterance.pitch = 1.1; // Gentle automated pitch
      window.speechSynthesis.speak(utterance);
    }
  };

  const startCall = () => {
    setCallActive(true);
    const greeting = 'Namaskara. How are you feeling today? You can speak naturally to me just like a phone call, or press the keypad buttons below.';
    setChatLog([{ 
      sender: 'ai', 
      text: greeting 
    }]);
    speakText(greeting);
  };

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatLog, isTyping]);

  const toggleListening = () => {
    if (!recognition) return;
    if (isListening) {
      recognition.stop();
      if (transcriptRef.current.trim()) {
        handleInput('voice', transcriptRef.current.trim());
      }
      setLiveTranscript('');
      transcriptRef.current = '';
    } else {
      setLiveTranscript('');
      transcriptRef.current = '';
      recognition.start();
    }
  };

  const handleInput = async (type, value) => {
    const newInteraction = { sender: 'patient', text: value };
    const currentLog = [...chatLog];
    
    // Optimistic UI Update
    setChatLog([...currentLog, newInteraction]);
    setIsTyping(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/demo/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          history: currentLog,
          latest_input: value
        }),
      });

      if (!response.ok) throw new Error('API Error');

      const data = await response.json();
      
      setSystemState({
        risk: data.risk_classification,
        keywords: data.detected_keywords,
        action: data.risk_classification === 'CRITICAL' ? 'Escalating Call to ASHA / Paramedic' : 'Logging Response'
      });

      setChatLog(prev => [...prev, { sender: 'ai', text: data.reply_text }]);
      speakText(data.reply_text);

      if (data.risk_classification === 'CRITICAL') {
        setTimeout(() => {
          setChatLog(prev => [...prev, { sender: 'system', text: 'Live Escalation: ASHA worker joined the call to assist.' }]);
          speakText("Your ASHA worker has joined the call. Generating summary overlay for paramedic integration.");
        }, 3000);
      }

    } catch (error) {
      console.error(error);
      const errText = "I'm having trouble connecting to the network. Could you please repeat that?";
      setChatLog(prev => [...prev, { sender: 'ai', text: errText }]);
      speakText(errText);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="patient-simulator container">
      <header className="page-header">
        <h2 className="text-gradient">Patient Simulator (Live Microphone Mode)</h2>
        <p className="text-secondary">Speak directly into your microphone to simulate a real patient voice call constraints.</p>
      </header>

      <div className="simulator-grid">
        <div className="phone-mockup glass-panel">
          <div className="phone-screen">
            {!callActive ? (
              <div className="incoming-call mt-12 text-center">
                <h3>SETU Health AI</h3>
                <p className="text-secondary mt-2">Incoming Call...</p>
                <button className="btn-primary mt-6 bounce-anim" onClick={startCall}>
                  Accept Call
                </button>
              </div>
            ) : (
              <div className="active-call" style={{height: '100%', display: 'flex', flexDirection: 'column'}}>
                <div className="chat-container">
                  {chatLog.map((msg, i) => (
                    <div key={i} className={`chat-bubble ${msg.sender}`}>
                      {msg.text}
                    </div>
                  ))}
                  {isTyping && (
                    <div className="chat-bubble ai typing-indicator">
                      <span className="dot"></span><span className="dot"></span><span className="dot"></span>
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </div>
                
                <div className="input-controls mt-auto">
                  <div className="voice-input text-center mb-4">
                    {recognition ? (
                      <div>
                        {liveTranscript && (
                          <div style={{color: 'var(--accent-primary)', marginBottom: '10px', fontStyle: 'italic', minHeight: '20px'}}>
                            "{liveTranscript}"
                          </div>
                        )}
                        <button 
                          className={`mic-button ${isListening ? 'listening heartbeat' : ''}`}
                          onClick={toggleListening}
                        >
                          {isListening ? (
                            <><span>🔴</span> <span style={{marginLeft: '8px'}}>Listening... Click to Submit</span></>
                          ) : (
                            <><span>🎙️</span> <span style={{marginLeft: '8px'}}>Tap to Speak</span></>
                          )}
                        </button>
                      </div>
                    ) : (
                      <p className="text-secondary" style={{fontSize: '0.8rem'}}>Browser doesn't support mic API.</p>
                    )}
                  </div>
                  
                  <div className="keypad-grid" style={{opacity: isListening ? 0.5 : 1, pointerEvents: isListening ? 'none' : 'auto'}}>
                    <button onClick={() => handleInput('button', '1 - I am fine')}>1 (Fine)</button>
                    <button onClick={() => handleInput('button', '2 - I have pain')}>2 (Pain)</button>
                    <button className="critical-btn" onClick={() => handleInput('button', '3 - Emergency')}>3 (Emergency)</button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="system-output glass-panel">
          <h3>Backend AI Engine Output</h3>
          <div className="output-field">
            <span className="label">Dynamically Detected Keywords:</span>
            <div className="keyword-tags">
              {systemState.keywords.length ? (
                systemState.keywords.map(kw => <span key={kw} className="tag">{kw}</span>)
              ) : <span className="text-secondary">None</span>}
            </div>
          </div>

          <div className="output-field">
            <span className="label">Classified Risk Level:</span>
            <div className={`risk-badge ${systemState.risk.toLowerCase()}`}>
              {systemState.risk}
            </div>
          </div>

          <div className="output-field">
            <span className="label">System Action Triggered:</span>
            <p className="action-text">{systemState.action}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

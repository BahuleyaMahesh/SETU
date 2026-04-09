import React from 'react'
import { Phone, Mic, Check } from 'lucide-react'

export default function PatientDetailCard({ patient }) {
  return (
    <div className="patient-card">
      <div className="card-header">
        <div className="patient-info">
          <h2>{patient.name}</h2>
          <p className="phone-number"><Phone size={14} /> {patient.phone}</p>
        </div>
        <div className={`status-badge large ${patient.status.toLowerCase()}`}>
          {patient.status}
        </div>
      </div>

      <div className="audio-section">
        <h3>Call Recording</h3>
        <div className="audio-player">
          <Mic size={20} color="var(--accent-primary)" />
          <div className="waveform">
            <div className="wave"></div><div className="wave"></div><div className="wave"></div>
            <div className="wave"></div><div className="wave"></div><div className="wave"></div>
          </div>
          <span className="duration">00:45</span>
        </div>
      </div>

      <div className="transcript-section">
        <h3>AI STT Transcript (Kannada &rarr; English)</h3>
        <div className="transcript-box">
          <p>"Namaskara, I am feeling very weak today and have a strong <strong>fever</strong> since the morning. I am also experiencing some <strong>chest pain</strong>."</p>
        </div>
      </div>

      <div className="ai-analysis">
        <h3>Rule Engine Mapping</h3>
        <ul className="mapping-logic">
          <li>Intent Evaluated: <code>Medical Issue Reporting</code></li>
          <li>Keywords Extracted: <code>{patient.symptoms.join(', ') || 'None'}</code></li>
          <li>Failsafe Route: {patient.status === 'CRITICAL' ? 'Escalated to PHC Doctor' : 'Logged for Local Worker'}</li>
        </ul>
      </div>

      <div className="actions">
        <button className="btn-primary flex-align">
          <Check size={18} style={{marginRight: '8px'}} /> Mark as Resolved
        </button>
        <button className="btn-secondary">Escalate to Doctor</button>
      </div>
    </div>
  )
}

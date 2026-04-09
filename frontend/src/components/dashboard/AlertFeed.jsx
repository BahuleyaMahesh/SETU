import React from 'react'
import { AlertCircle, AlertTriangle, CheckCircle } from 'lucide-react'

const MOCK_ALERTS = [
  { id: 1, name: 'Siddaramaiah', phone: '+91 98450 XXXXX', status: 'CRITICAL', time: '2 mins ago', symptoms: ['Chest Pain', 'Fever'] },
  { id: 2, name: 'Lakshmamma', phone: '+91 80500 XXXXX', status: 'WARNING', time: '15 mins ago', symptoms: ['Dizziness'] },
  { id: 3, name: 'Ramesh T.', phone: '+91 99011 XXXXX', status: 'NORMAL', time: '1 hour ago', symptoms: [] },
]

export default function AlertFeed({ onSelectPatient }) {
  return (
    <div className="alert-list">
      {MOCK_ALERTS.map(alert => (
        <div 
          key={alert.id} 
          className={`alert-item glass-panel ${alert.status === 'CRITICAL' ? 'alert-critical' : alert.status === 'WARNING' ? 'alert-warning' : ''}`}
          onClick={() => onSelectPatient(alert)}
        >
          <div className="alert-header">
            <h4>{alert.name}</h4>
            <span className="alert-time">{alert.time}</span>
          </div>
          <div className="alert-phone">{alert.phone}</div>
          
          <div className="alert-footer">
            <div className="alert-badge" data-status={alert.status}>
              {alert.status === 'CRITICAL' && <AlertCircle size={14} />}
              {alert.status === 'WARNING' && <AlertTriangle size={14} />}
              {alert.status === 'NORMAL' && <CheckCircle size={14} />}
              <span>{alert.status}</span>
            </div>
            {alert.symptoms.length > 0 && (
              <div className="symptom-tags">
                {alert.symptoms.map((s, i) => <span key={i} className="tag">{s}</span>)}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

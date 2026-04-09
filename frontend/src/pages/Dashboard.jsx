import React, { useState } from 'react'
import AlertFeed from '../components/dashboard/AlertFeed'
import PatientDetailCard from '../components/dashboard/PatientDetailCard'
import './Dashboard.css'

export default function Dashboard() {
  const [selectedPatient, setSelectedPatient] = useState(null)

  const handleSelectPatient = (patient) => {
    setSelectedPatient(patient)
  }

  return (
    <div className="dashboard container">
      <header className="dashboard-header">
        <h2>ASHA Worker Command Center</h2>
        <p className="text-secondary">Monitoring rural populations across 3 PHCs</p>
      </header>

      <div className="dashboard-grid">
        <aside className="dashboard-feed glass-panel">
          <h3>Live Alert Feed</h3>
          <AlertFeed onSelectPatient={handleSelectPatient} />
        </aside>
        
        <main className="dashboard-detail glass-panel">
          {selectedPatient ? (
            <PatientDetailCard patient={selectedPatient} />
          ) : (
            <div className="empty-state">
              <p>Select a patient alert to view details, audio transcripts, and AI analysis.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

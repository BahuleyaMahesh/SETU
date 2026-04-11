import React from 'react';
import './Dashboard.css';

export default function AdminDashboard() {
  return (
    <div className="dashboard container">
      <header className="dashboard-header">
        <h2 className="text-gradient">Hospital Administration Command Center</h2>
        <p className="text-secondary">System-wide monitoring, analytics, and policy deployment</p>
      </header>

      <div className="admin-stats-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginTop: '2rem' }}>
        <div className="glass-panel" style={{ padding: '1.5rem', textAlign: 'center' }}>
          <h3 style={{ color: 'var(--text-secondary)' }}>Total Monitored Patients</h3>
          <p style={{ fontSize: '2.5rem', fontWeight: 'bold', marginTop: '1rem' }}>4,213</p>
        </div>
        <div className="glass-panel" style={{ padding: '1.5rem', textAlign: 'center' }}>
          <h3 style={{ color: 'var(--text-secondary)' }}>CRITICAL Escalations (24h)</h3>
          <p style={{ fontSize: '2.5rem', fontWeight: 'bold', marginTop: '1rem', color: 'var(--critical-red)' }}>12</p>
        </div>
        <div className="glass-panel" style={{ padding: '1.5rem', textAlign: 'center' }}>
          <h3 style={{ color: 'var(--text-secondary)' }}>ASHA Worker Utilization</h3>
          <p style={{ fontSize: '2.5rem', fontWeight: 'bold', marginTop: '1rem', color: 'var(--success-green)' }}>89%</p>
        </div>
      </div>

      <div style={{ marginTop: '3rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>Recent Critical Flags (Across all PHCs)</h3>
        <div className="glass-panel" style={{ padding: '1rem' }}>
          <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                <th style={{ padding: '1rem' }}>Patient ID</th>
                <th style={{ padding: '1rem' }}>Village / PHC</th>
                <th style={{ padding: '1rem' }}>Assigned ASHA</th>
                <th style={{ padding: '1rem' }}>AI Symptom Risk</th>
                <th style={{ padding: '1rem' }}>Action Taken</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ padding: '1rem' }}>#PT-9932</td>
                <td style={{ padding: '1rem' }}>Hassan North</td>
                <td style={{ padding: '1rem' }}>Radha S.</td>
                <td style={{ padding: '1rem', color: 'var(--critical-red)' }}>Severe breathlessness</td>
                <td style={{ padding: '1rem' }}><button className="btn-secondary" style={{ padding: '0.4rem 1rem', fontSize: '0.8rem' }}>View Call Transcript</button></td>
              </tr>
              <tr>
                <td style={{ padding: '1rem' }}>#PT-1032</td>
                <td style={{ padding: '1rem' }}>Mandya Rural</td>
                <td style={{ padding: '1rem' }}>Lakshmi M.</td>
                <td style={{ padding: '1rem', color: 'var(--warning-yellow)' }}>Persistent Fever</td>
                <td style={{ padding: '1rem' }}><button className="btn-secondary" style={{ padding: '0.4rem 1rem', fontSize: '0.8rem' }}>View Call Transcript</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

import React from 'react'
import { Link } from 'react-router-dom'
import { PhoneCall, ShieldAlert, Cpu } from 'lucide-react'
import './Landing.css'

export default function Landing() {
  return (
    <div className="landing">
      {/* Hero Section */}
      <section className="hero container">
        <div className="hero-content">
          <h1 className="hero-title">
            AI-Powered Patient Monitoring <br />
            <span className="text-gradient">For Rural Healthcare</span>
          </h1>
          <p className="hero-subtitle">
            SETU enables low-cost, automated post-discharge care via voice and feature phones. 
            No internet, no smartphone needed. We listen, understand, and escalate.
          </p>
          <div className="hero-actions">
            <Link to="/dashboard" className="btn-primary" style={{ display: 'inline-block', textDecoration: 'none' }}>
              View Dashboard
            </Link>
          </div>
        </div>
        <div className="hero-visual">
          <div className="glass-panel image-container">
             <img src="/hero.png" alt="SETU Architecture Mockup" className="hero-img" />
             <div className="glow-effect"></div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features container">
        <h2 className="section-title text-center">How It Works</h2>
        <div className="feature-grid">
          <div className="feature-card glass-panel">
            <div className="feature-icon"><PhoneCall size={32} color="var(--accent-primary)" /></div>
            <h3>Zero-Cost Missed Calls</h3>
            <p>Patients trigger the system by giving a missed call. SETU automatically calls them back across 2G networks.</p>
          </div>
          <div className="feature-card glass-panel">
            <div className="feature-icon"><Cpu size={32} color="var(--accent-primary)" /></div>
            <h3>Native Language AI</h3>
            <p>Conversations are transcribed using state-of-the-art Speech-to-Text and interpreted for symptoms.</p>
          </div>
          <div className="feature-card glass-panel">
            <div className="feature-icon"><ShieldAlert size={32} color="#ef4444" /></div>
            <h3>Rule-Based Failsafes</h3>
            <p>Critical keywords instantly bypass AI to alert ASHA workers and local hospitals in real-time.</p>
          </div>
        </div>
      </section>
    </div>
  )
}

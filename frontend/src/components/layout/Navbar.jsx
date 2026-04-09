import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Activity } from 'lucide-react'
import './Navbar.css'

export default function Navbar() {
  const location = useLocation()

  return (
    <nav className="navbar glass-panel">
      <div className="container nav-content">
        <Link to="/" className="nav-logo">
          <Activity size={28} className="logo-icon" color="var(--accent-primary)" />
          <span>SETU</span>
        </Link>
        <div className="nav-links">
          <Link to="/" className={location.pathname === '/' ? 'active' : ''}>Home</Link>
          <Link to="/features">Features</Link>
          <Link to="/dashboard" className={`btn-primary ${location.pathname === '/dashboard' ? 'active-btn' : ''}`}>
            Access Dashboard
          </Link>
        </div>
      </div>
    </nav>
  )
}

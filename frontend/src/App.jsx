import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Navbar from './components/layout/Navbar'
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import PatientSimulator from './pages/PatientSimulator'
import AdminDashboard from './pages/AdminDashboard'
import './index.css'

function App() {
  return (
    <Router>
      <div className="app-wrapper">
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/demo" element={<PatientSimulator />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App

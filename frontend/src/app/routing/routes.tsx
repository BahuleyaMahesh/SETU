import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Auth pages
import { Login } from '../../features/auth/pages/Login';

// Patient pages
import { PatientLayout } from '../layouts/PatientLayout';
import { PatientHome } from '../../features/patient/pages/Home';
import { PatientCheckup } from '../../features/patient/pages/Checkup';
import { PatientReminders } from '../../features/patient/pages/Reminders';
import { PatientChat } from '../../features/patient/pages/Chat';
import { PatientProfile } from '../../features/patient/pages/Profile';
import { PatientPrescriptions } from '../../features/patient/pages/Prescriptions';

// ASHA pages
import { AshaLayout } from '../layouts/AshaLayout';
import { AshaHome } from '../../features/asha/pages/Home';
import { AshaPatients } from '../../features/asha/pages/Patients';
import { AshaPatientDetail } from '../../features/asha/pages/PatientDetail';
import { AshaMap } from '../../features/asha/pages/Map';
import { AshaAlerts } from '../../features/asha/pages/Alerts';

// Hospital pages
import { HospitalLayout } from '../layouts/HospitalLayout';
import { HospitalDashboard } from '../../features/hospital/pages/Dashboard';
import { HospitalPatients } from '../../features/hospital/pages/Patients';
import { HospitalAlertQueue } from '../../features/hospital/pages/AlertQueue';
import { HospitalAnalytics } from '../../features/hospital/pages/Analytics';
import { HospitalReports } from '../../features/hospital/pages/Reports';
import { HospitalMap } from '../../features/hospital/pages/Map';

// Shared staff chat (ASHA + Hospital)
import { StaffPatientChat } from '../../features/chat/StaffPatientChat';

import ProtectedRoute from './ProtectedRoute';
import RoleRoute from './RoleRoute';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<Login />} />
      <Route path="/login" element={<Login />} />

      {/* Patient routes */}
      <Route
        path="/patient/*"
        element={
          <ProtectedRoute>
            <RoleRoute role="patient">
              <PatientLayout>
                <Routes>
                  <Route path="home" element={<PatientHome />} />
                  <Route path="checkup" element={<PatientCheckup />} />
                  <Route path="reminders" element={<PatientReminders />} />
                  <Route path="prescriptions" element={<PatientPrescriptions />} />
                  <Route path="chat" element={<PatientChat />} />
                  <Route path="profile" element={<PatientProfile />} />
                  <Route path="*" element={<Navigate to="home" replace />} />
                </Routes>
              </PatientLayout>
            </RoleRoute>
          </ProtectedRoute>
        }
      />

      {/* ASHA routes */}
      <Route
        path="/asha/*"
        element={
          <ProtectedRoute>
            <RoleRoute role="asha">
              <AshaLayout>
                <Routes>
                  <Route path="home" element={<AshaHome />} />
                  <Route path="patients" element={<AshaPatients />} />
                  <Route path="patients/:patientId" element={<AshaPatientDetail />} />
                  <Route path="map" element={<AshaMap />} />
                  <Route path="alerts" element={<AshaAlerts />} />
                  <Route path="assistant" element={<StaffPatientChat />} />
                  <Route path="*" element={<Navigate to="home" replace />} />
                </Routes>
              </AshaLayout>
            </RoleRoute>
          </ProtectedRoute>
        }
      />

      {/* Hospital routes */}
      <Route
        path="/hospital/*"
        element={
          <ProtectedRoute>
            <RoleRoute role="hospital">
              <HospitalLayout>
                <Routes>
                  <Route path="dashboard" element={<HospitalDashboard />} />
                  <Route path="patients" element={<HospitalPatients />} />
                  <Route path="alerts" element={<HospitalAlertQueue />} />
                  <Route path="analytics" element={<HospitalAnalytics />} />
                  <Route path="reports" element={<HospitalReports />} />
                  <Route path="map" element={<HospitalMap />} />
                  <Route path="assistant" element={<StaffPatientChat />} />
                  <Route path="*" element={<Navigate to="dashboard" replace />} />
                </Routes>
              </HospitalLayout>
            </RoleRoute>
          </ProtectedRoute>
        }
      />

      {/* Catch-all redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

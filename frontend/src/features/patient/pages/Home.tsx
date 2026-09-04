import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../app/auth/AuthProvider';
import { Card } from '../../../shared/components/Card';
import { Button } from '../../../shared/components/Button';
import { Badge } from '../../../shared/components/Badge';
import { ClipboardList, Bell, MessageSquare, HeartPulse, UserCheck, ShieldAlert, Building2, Navigation, Phone } from 'lucide-react';
import { PatientMap, MapMarker } from '../../maps/components/PatientMap';
import { mapsApi, NearbyHospital } from '../../maps/api';

export const PatientHome: React.FC = () => {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [healthData, setHealthData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [nearbyHospitals, setNearbyHospitals] = useState<NearbyHospital[]>([]);
  const [hospitalsLoading, setHospitalsLoading] = useState(true);

  useEffect(() => {
    if (!token || !user?.patient_id) {
      setLoading(false);
      return;
    }
    fetchHealthData();
    mapsApi.getNearbyHospitals(user.patient_id, 3)
      .then((data) => setNearbyHospitals(data.hospitals || []))
      .catch((err) => console.error('Error loading nearby hospitals:', err))
      .finally(() => setHospitalsLoading(false));
  }, [token, user?.patient_id]);

  const fetchHealthData = async () => {
    try {
      const response = await fetch(`/api/v1/patients/${user?.patient_id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setHealthData(data);
      }
    } catch (error) {
      console.error('Error fetching health data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-16">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600" />
      </div>
    );
  }

  const riskLevel = healthData?.risk_level || 'normal';

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-sky-600 to-teal-600 text-white rounded-2xl p-6 shadow-md">
        <h1 className="text-2xl font-bold tracking-tight">
          Welcome back, {user?.full_name || 'Patient'}
        </h1>
        <p className="text-sky-100 text-sm mt-1">
          SETU continuous health monitoring is active. Submit daily check-ins to stay connected with your care team.
        </p>
      </div>

      {/* Health Overview */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            <HeartPulse className="w-5 h-5 text-sky-600" />
            <span>Health Status Overview</span>
          </h2>
          <Badge variant={riskLevel === 'critical' ? 'danger' : riskLevel === 'warning' ? 'warning' : 'success'}>
            {riskLevel.toUpperCase()}
          </Badge>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Assigned Risk Tier</p>
            <p className={`text-xl font-bold mt-1 capitalize ${
              riskLevel === 'critical' ? 'text-red-600' :
              riskLevel === 'warning' ? 'text-amber-600' : 'text-emerald-600'
            }`}>
              {riskLevel} Risk
            </p>
          </div>

          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Latest Check-in</p>
            <p className="text-xl font-bold text-slate-800 mt-1">
              {healthData?.last_checkin ? new Date(healthData.last_checkin).toLocaleDateString() : 'Pending Today'}
            </p>
          </div>
        </div>
      </Card>

      {/* Quick Action Navigation */}
      <Card className="p-6">
        <h3 className="text-lg font-bold text-slate-800 mb-4">Recommended Actions</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <Button
            onClick={() => navigate('/patient/checkup')}
            className="w-full bg-sky-600 hover:bg-sky-500 text-white font-semibold py-3 rounded-xl flex items-center justify-center gap-2 shadow-sm"
          >
            <ClipboardList className="w-5 h-5" />
            <span>New Check-in</span>
          </Button>

          <Button
            onClick={() => navigate('/patient/reminders')}
            variant="outline"
            className="w-full font-semibold py-3 rounded-xl flex items-center justify-center gap-2 border-slate-300 hover:bg-slate-50"
          >
            <Bell className="w-5 h-5 text-slate-600" />
            <span>View Reminders</span>
          </Button>

          <Button
            onClick={() => navigate('/patient/chat')}
            variant="outline"
            className="w-full font-semibold py-3 rounded-xl flex items-center justify-center gap-2 border-slate-300 hover:bg-slate-50"
          >
            <MessageSquare className="w-5 h-5 text-slate-600" />
            <span>AI Care Assistant</span>
          </Button>
        </div>
      </Card>

      {/* Assigned ASHA Worker */}
      <Card className="p-6">
        <h3 className="text-lg font-bold text-slate-800 mb-3 flex items-center gap-2">
          <UserCheck className="w-5 h-5 text-teal-600" />
          <span>Assigned ASHA Field Worker</span>
        </h3>
        {healthData?.asha_worker ? (
          <div className="flex items-center justify-between bg-teal-50/60 dark:bg-teal-950/40 border border-teal-200/60 dark:border-teal-800/40 p-4 rounded-xl">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-teal-600 text-white font-bold rounded-xl flex items-center justify-center text-lg shadow-sm">
                {healthData.asha_worker.full_name?.[0] || 'A'}
              </div>
              <div>
                <p className="font-semibold text-slate-900">
                  {healthData.asha_worker.full_name}
                </p>
                <p className="text-xs text-teal-700 mt-0.5">
                  District: {healthData.asha_worker.district || 'Mandya'}
                </p>
              </div>
            </div>
            {healthData.asha_worker.phone && (
              <a
                href={`tel:${healthData.asha_worker.phone}`}
                className="flex items-center gap-2 px-3 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-lg font-medium text-xs shadow-sm transition-colors"
              >
                <Phone className="w-3.5 h-3.5" />
                <span>{healthData.asha_worker.phone}</span>
              </a>
            )}
          </div>
        ) : (
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-slate-500 text-sm">
            No ASHA worker currently assigned to your care profile.
          </div>
        )}
      </Card>

      {/* Nearby Hospitals */}
      <Card className="p-6">
        <h3 className="text-lg font-bold text-slate-800 mb-3 flex items-center gap-2">
          <Building2 className="w-5 h-5 text-sky-600" />
          <span>Nearest Hospitals</span>
        </h3>
        {hospitalsLoading ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">Finding nearby hospitals…</p>
        ) : nearbyHospitals.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">
            No hospitals found nearby. Contact your ASHA worker if you need directions to care.
          </p>
        ) : (
          <div className="space-y-4">
            <PatientMap
              markers={[
                ...(healthData?.latitude
                  ? [{ id: 'me', lat: healthData.latitude, lng: healthData.longitude, label: 'Your location', color: '#0ea5e9' } as MapMarker]
                  : []),
                ...nearbyHospitals.map((h) => ({
                  id: h.id,
                  lat: h.latitude,
                  lng: h.longitude,
                  label: h.name,
                  sublabel: `${h.distance_km} km away`,
                  color: '#dc2626',
                })),
              ]}
              height="260px"
            />
            <div className="space-y-2">
              {nearbyHospitals.map((h, i) => (
                <div key={h.id} className="flex items-center justify-between p-3 border border-slate-200 dark:border-slate-700 rounded-xl">
                  <div>
                    <p className="text-sm font-semibold text-slate-800">{i === 0 && '⭐ '}{h.name}</p>
                    <p className="text-xs text-slate-500">{h.address} · {h.distance_km} km</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {h.contact_phone && (
                      <a href={`tel:${h.contact_phone}`} className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300" title="Call">
                        <Phone className="w-4 h-4" />
                      </a>
                    )}
                    <a
                      href={`https://www.google.com/maps/dir/?api=1&destination=${h.latitude},${h.longitude}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 rounded-lg bg-sky-100 dark:bg-sky-950 text-sky-700 dark:text-sky-400"
                      title="Get directions"
                    >
                      <Navigation className="w-4 h-4" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

export default PatientHome;

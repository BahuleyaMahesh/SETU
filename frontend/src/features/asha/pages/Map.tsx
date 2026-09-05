import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from '../../../shared/components/Card';
import { Badge } from '../../../shared/components/Badge';
import { PatientMap, MapMarker } from '../../maps/components/PatientMap';
import { mapsApi, NearbyHospital } from '../../maps/api';
import { Building2, Phone, Navigation } from 'lucide-react';

interface AshaPatient {
  id: string;
  mrn: string;
  full_name: string;
  village: string;
  risk_level: string;
  latitude: number | null;
  longitude: number | null;
}

const riskColor = (risk: string) =>
  risk === 'critical' ? '#ef4444' : risk === 'warning' ? '#f59e0b' : '#10b981';

export const AshaMap: React.FC = () => {
  const [patients, setPatients] = useState<AshaPatient[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedPatientId, setSelectedPatientId] = useState('');
  const [nearbyHospitals, setNearbyHospitals] = useState<NearbyHospital[]>([]);
  const [loadingHospitals, setLoadingHospitals] = useState(false);

  useEffect(() => {
    mapsApi.getAshaPatients()
      .then((data) => setPatients(data.patients || []))
      .catch((err) => console.error('Error loading ASHA map data:', err))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedPatientId) {
      setNearbyHospitals([]);
      return;
    }
    setLoadingHospitals(true);
    mapsApi.getNearbyHospitals(selectedPatientId, 5)
      .then((data) => setNearbyHospitals(data.hospitals || []))
      .catch((err) => console.error('Error loading nearby hospitals:', err))
      .finally(() => setLoadingHospitals(false));
  }, [selectedPatientId]);

  const selectedPatient = patients.find((p) => p.id === selectedPatientId);

  const markers: MapMarker[] = [
    ...patients
      .filter((p) => p.latitude != null && p.longitude != null)
      .map((p) => ({
        id: p.id,
        lat: p.latitude as number,
        lng: p.longitude as number,
        label: p.full_name,
        sublabel: `${p.risk_level} · ${p.village}`,
        color: riskColor(p.risk_level),
      })),
    ...nearbyHospitals
      .filter((h) => h.latitude != null && h.longitude != null)
      .map((h) => ({
        id: `hospital-${h.id}`,
        lat: h.latitude,
        lng: h.longitude,
        label: h.name,
        sublabel: `${h.distance_km} km away`,
        color: '#0284c7',
      })),
  ];

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-semibold">Patient Locations</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-2">
          <Card className="h-[600px]">
            <CardHeader>
              <h2 className="text-lg font-medium">Patient Map</h2>
            </CardHeader>
            <CardContent className="h-[calc(100%-65px)]">
              {loading ? (
                <div className="flex items-center justify-center h-full text-slate-400">Loading map…</div>
              ) : (
                <PatientMap markers={markers} height="100%" />
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <h2 className="text-lg font-medium">Patient Summary</h2>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {patients.map((patient) => (
                  <div
                    key={patient.id}
                    onClick={() => setSelectedPatientId(patient.id)}
                    className={`flex items-center gap-3 p-2 rounded cursor-pointer transition-colors ${
                      selectedPatientId === patient.id ? 'bg-sky-50 dark:bg-sky-950/40 ring-1 ring-sky-400' : 'hover:bg-gray-50'
                    }`}
                  >
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-medium ${
                      patient.risk_level === 'critical' ? 'bg-red-500' : patient.risk_level === 'warning' ? 'bg-yellow-500' : 'bg-green-500'
                    }`}>
                      {patient.full_name.charAt(0)}
                    </div>
                    <div className="flex-1">
                      <div className="text-sm font-medium">{patient.full_name}</div>
                      <div className="text-xs text-gray-500">{patient.village}</div>
                    </div>
                    <Badge variant={patient.risk_level === 'critical' ? 'danger' : patient.risk_level === 'warning' ? 'warning' : 'success'}>
                      {patient.risk_level}
                    </Badge>
                  </div>
                ))}
                {patients.length === 0 && !loading && (
                  <p className="text-sm text-gray-500 dark:text-slate-400">No assigned patients found.</p>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <h2 className="text-lg font-medium flex items-center gap-2">
                <Building2 className="w-4 h-4 text-sky-600" />
                Nearest Hospitals
              </h2>
            </CardHeader>
            <CardContent>
              {!selectedPatientId && (
                <p className="text-sm text-gray-500 dark:text-slate-400">Select a patient above to find their nearest hospitals.</p>
              )}
              {selectedPatientId && loadingHospitals && (
                <p className="text-sm text-gray-500 dark:text-slate-400">Finding nearby hospitals…</p>
              )}
              {selectedPatientId && !loadingHospitals && (
                <div className="space-y-2">
                  {selectedPatient && (
                    <p className="text-xs text-gray-500 dark:text-slate-400 mb-2">For {selectedPatient.full_name}</p>
                  )}
                  {nearbyHospitals.map((h, i) => (
                    <div key={h.id} className="p-3 border border-gray-200 dark:border-slate-700 rounded-lg">
                      <div className="flex justify-between items-start">
                        <div className="font-medium text-sm">{i === 0 && '⭐ '}{h.name}</div>
                        <span className="text-xs font-semibold text-sky-600 whitespace-nowrap">{h.distance_km} km</span>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">{h.address}</p>
                      {h.contact_phone && (
                        <a href={`tel:${h.contact_phone}`} className="text-xs text-sky-600 flex items-center gap-1 mt-1">
                          <Phone className="w-3 h-3" /> {h.contact_phone}
                        </a>
                      )}
                      <a
                        href={`https://www.google.com/maps/dir/?api=1&destination=${h.latitude},${h.longitude}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-emerald-600 flex items-center gap-1 mt-1"
                      >
                        <Navigation className="w-3 h-3" /> Get Directions
                      </a>
                    </div>
                  ))}
                  {nearbyHospitals.length === 0 && (
                    <p className="text-sm text-gray-500 dark:text-slate-400">No hospitals found, or this patient has no location on file.</p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AshaMap;

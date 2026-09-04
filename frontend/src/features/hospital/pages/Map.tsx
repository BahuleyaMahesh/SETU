import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from '../../../shared/components/Card';
import { Badge } from '../../../shared/components/Badge';
import { Button } from '../../../shared/components/Button';
import { PatientMap, MapMarker } from '../../maps/components/PatientMap';
import { mapsApi, GeocodeResult } from '../../maps/api';
import { apiClient } from '../../../shared/utils/api';
import { Search, MapPin, Loader2 } from 'lucide-react';

interface HospitalPatient {
  id: string;
  mrn: string;
  full_name: string;
  village: string;
  address?: string;
  risk_level: string;
  latitude: number | null;
  longitude: number | null;
}

const riskColor = (risk: string) =>
  risk === 'critical' ? '#ef4444' : risk === 'warning' ? '#f59e0b' : '#10b981';

export const HospitalMap: React.FC = () => {
  const [patients, setPatients] = useState<HospitalPatient[]>([]);
  const [hospital, setHospital] = useState<{ id: string; name: string; latitude: number; longitude: number } | null>(null);
  const [loading, setLoading] = useState(true);

  // "Pin a patient's location" flow
  const [selectedPatientId, setSelectedPatientId] = useState('');
  const [addressQuery, setAddressQuery] = useState('');
  const [searchResults, setSearchResults] = useState<GeocodeResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [pendingLocation, setPendingLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');

  useEffect(() => {
    loadPatients();
  }, []);

  const loadPatients = async () => {
    setLoading(true);
    try {
      const data = await mapsApi.getHospitalPatients();
      setPatients(data.patients || []);
      setHospital(data.hospital || null);
    } catch (error) {
      console.error('Error loading hospital map data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchAddress = async () => {
    if (!addressQuery.trim()) return;
    setSearching(true);
    setSearchResults([]);
    try {
      const data = await mapsApi.geocode(addressQuery);
      setSearchResults(data.results || []);
    } catch (error) {
      console.error('Geocode error:', error);
    } finally {
      setSearching(false);
    }
  };

  const handleSaveLocation = async () => {
    if (!selectedPatientId || !pendingLocation) return;
    setSaving(true);
    setSaveMessage('');
    try {
      await apiClient.put(`/api/v1/patients/${selectedPatientId}`, {
        latitude: pendingLocation.lat,
        longitude: pendingLocation.lng,
      });
      setSaveMessage('Location saved.');
      setPendingLocation(null);
      setSearchResults([]);
      setAddressQuery('');
      await loadPatients();
    } catch (error: any) {
      setSaveMessage(error.message || 'Failed to save location.');
    } finally {
      setSaving(false);
    }
  };

  const markers: MapMarker[] = [
    ...(hospital && hospital.latitude != null
      ? [{ id: `hospital-${hospital.id}`, lat: hospital.latitude, lng: hospital.longitude, label: hospital.name, sublabel: 'Hospital', color: '#0284c7' }]
      : []),
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
    ...(pendingLocation
      ? [{ id: 'pending', lat: pendingLocation.lat, lng: pendingLocation.lng, label: 'New location (unsaved)', color: '#a855f7' }]
      : []),
  ];

  const criticalPatients = patients.filter((p) => p.risk_level === 'critical');
  const patientsMissingLocation = patients.filter((p) => p.latitude == null || p.longitude == null);

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-semibold">Patient Locations</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 space-y-4">
          <Card className="h-[500px]">
            <CardHeader>
              <h2 className="text-lg font-medium">Hospital Patient Map</h2>
            </CardHeader>
            <CardContent className="h-[calc(100%-65px)]">
              {loading ? (
                <div className="flex items-center justify-center h-full text-slate-400">Loading map…</div>
              ) : (
                <PatientMap
                  markers={markers}
                  height="100%"
                  onMapClick={(lat, lng) => setPendingLocation({ lat, lng })}
                />
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <h2 className="text-lg font-medium">Pin a Patient's Location</h2>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-xs text-gray-500 dark:text-slate-400">
                Search an address, or click directly on the map above to drop a pin — then choose which patient it belongs to and save.
              </p>

              <div className="flex gap-2">
                <input
                  type="text"
                  value={addressQuery}
                  onChange={(e) => setAddressQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearchAddress()}
                  placeholder="Search an address (e.g. village, district)…"
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-gray-900 dark:text-slate-100 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <Button size="sm" onClick={handleSearchAddress} disabled={searching}>
                  {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                </Button>
              </div>

              {searchResults.length > 0 && (
                <div className="border border-gray-200 dark:border-slate-700 rounded-lg divide-y divide-gray-200 dark:divide-slate-700 max-h-40 overflow-y-auto">
                  {searchResults.map((r, i) => (
                    <button
                      key={i}
                      onClick={() => { setPendingLocation({ lat: r.latitude, lng: r.longitude }); setSearchResults([]); }}
                      className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-slate-800 flex items-start gap-2"
                    >
                      <MapPin className="w-4 h-4 mt-0.5 shrink-0 text-gray-400" />
                      <span>{r.display_name}</span>
                    </button>
                  ))}
                </div>
              )}

              {pendingLocation && (
                <div className="p-3 bg-purple-50 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-800 rounded-lg space-y-2">
                  <p className="text-xs text-purple-800 dark:text-purple-300">
                    Pinned: {pendingLocation.lat.toFixed(5)}, {pendingLocation.lng.toFixed(5)}
                  </p>
                  <select
                    value={selectedPatientId}
                    onChange={(e) => setSelectedPatientId(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg text-sm"
                  >
                    <option value="">Select patient…</option>
                    {patients.map((p) => (
                      <option key={p.id} value={p.id}>{p.full_name} ({p.mrn})</option>
                    ))}
                  </select>
                  <div className="flex gap-2">
                    <Button size="sm" onClick={handleSaveLocation} disabled={!selectedPatientId || saving}>
                      {saving ? 'Saving…' : 'Save Location'}
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => setPendingLocation(null)}>Cancel</Button>
                  </div>
                </div>
              )}

              {saveMessage && <p className="text-xs text-gray-500 dark:text-slate-400">{saveMessage}</p>}

              {patientsMissingLocation.length > 0 && (
                <p className="text-xs text-amber-600 dark:text-amber-400">
                  {patientsMissingLocation.length} patient(s) have no location on file yet.
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <h2 className="text-lg font-medium">Critical Patients</h2>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {criticalPatients.length === 0 && (
                  <p className="text-sm text-gray-500 dark:text-slate-400">No critical patients right now.</p>
                )}
                {criticalPatients.map((patient) => (
                  <div key={patient.id} className="flex items-center gap-3 p-2 bg-red-50 rounded">
                    <div className="w-8 h-8 rounded-full bg-red-500 flex items-center justify-center text-white text-xs font-medium">
                      {patient.full_name.charAt(0)}
                    </div>
                    <div className="flex-1">
                      <div className="text-sm font-medium">{patient.full_name}</div>
                      <div className="text-xs text-red-600">{patient.village}</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <h2 className="text-lg font-medium">Statistics</h2>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Total Patients</span>
                  <span className="font-medium">{patients.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Critical</span>
                  <span className="font-medium text-red-500">
                    {patients.filter((p) => p.risk_level === 'critical').length}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Warning</span>
                  <span className="font-medium text-yellow-500">
                    {patients.filter((p) => p.risk_level === 'warning').length}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">Normal</span>
                  <span className="font-medium text-green-500">
                    {patients.filter((p) => p.risk_level === 'normal').length}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default HospitalMap;

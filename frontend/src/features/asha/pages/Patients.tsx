import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from '../../../shared/components/Card';
import { Badge } from '../../../shared/components/Badge';
import { Button } from '../../../shared/components/Button';
import { Input } from '../../../shared/components/Input';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../app/auth/AuthProvider';
import { UserPlus, UserX, MapPin, Search, AlertCircle, CheckCircle2 } from 'lucide-react';
import { PatientMap, MapMarker } from '../../maps/components/PatientMap';
import { mapsApi } from '../../maps/api';

interface PatientItem {
  id: string;
  mrn: string;
  full_name: string;
  age?: number;
  gender?: string;
  phone: string;
  address?: string;
  village?: string;
  district?: string;
  state?: string;
  pincode?: string;
  latitude?: number;
  longitude?: number;
  risk_level: string;
  last_checkin?: string;
}

export const AshaPatients: React.FC = () => {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [patients, setPatients] = useState<PatientItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const [formData, setFormData] = useState<{
    patient_id: string;
    full_name: string;
    phone: string;
    email: string;
    password: string;
    age: string;
    gender: string;
    condition: string;
    symptoms: string;
    address: string;
    village: string;
    district: string;
    state: string;
    pincode: string;
    latitude?: number;
    longitude?: number;
  }>({
    patient_id: '',
    full_name: '',
    phone: '',
    email: '',
    password: 'Patient@123',
    age: '',
    gender: 'Male',
    condition: '',
    symptoms: '',
    address: '',
    village: '',
    district: '',
    state: 'Karnataka',
    pincode: '',
    latitude: undefined,
    longitude: undefined,
  });

  const fetchPatients = async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const ashaId = user?.asha_worker_id || 'default';
      const response = await fetch(`/api/v1/asha/${ashaId}/patients`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setPatients(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error('Failed to fetch ASHA patients:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPatients();
    // Auto-open modal if URL contains ?add=true
    if (window.location.search.includes('add=true')) {
      setShowAddModal(true);
    }
  }, [token, user?.asha_worker_id]);

  const handleSelectExisting = (patientId: string) => {
    if (!patientId) {
      setFormData({
        patient_id: '',
        full_name: '',
        phone: '',
        email: '',
        password: 'Patient@123',
        age: '',
        gender: 'Male',
        condition: '',
        symptoms: '',
        address: '',
        village: '',
        district: '',
        state: 'Karnataka',
        pincode: '',
        latitude: 12.9716,
        longitude: 77.5946,
      });
      return;
    }
    const found = patients.find((p) => p.id === patientId);
    if (found) {
      setFormData((prev) => ({
        ...prev,
        patient_id: found.id,
        full_name: found.full_name || '',
        phone: found.phone || '',
        age: found.age ? String(found.age) : '',
        gender: found.gender || 'Male',
        address: found.address || '',
        village: found.village || '',
        district: found.district || '',
        state: found.state || 'Karnataka',
        pincode: found.pincode || '',
        latitude: found.latitude ? Number(found.latitude) : 12.9716,
        longitude: found.longitude ? Number(found.longitude) : 77.5946,
      }));
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleGeocode = async () => {
    const query = [formData.address, formData.village, formData.district, formData.state].filter(Boolean).join(', ');
    if (!query) return;
    try {
      const res = await mapsApi.geocode(query);
      if (res.results && res.results.length > 0) {
        setFormData((prev) => ({
          ...prev,
          latitude: res.results[0].latitude,
          longitude: res.results[0].longitude,
        }));
      }
    } catch (err) {
      console.error('Geocoding error:', err);
    }
  };

  const handleAddPatient = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');
    setIsSubmitting(true);
    try {
      const response = await fetch('/api/v1/asha/patients', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          ...formData,
          age: formData.age ? parseInt(formData.age, 10) : undefined,
          latitude: formData.latitude ? parseFloat(String(formData.latitude)) : undefined,
          longitude: formData.longitude ? parseFloat(String(formData.longitude)) : undefined,
        }),
      });

      if (response.ok) {
        setSuccessMsg(formData.patient_id ? 'Patient details updated successfully!' : 'Patient successfully registered & assigned!');
        setShowAddModal(false);
        setFormData({
          patient_id: '',
          full_name: '',
          phone: '',
          email: '',
          password: 'Patient@123',
          age: '',
          gender: 'Male',
          condition: '',
          symptoms: '',
          address: '',
          village: '',
          district: '',
          state: 'Karnataka',
          pincode: '',
          latitude: undefined,
          longitude: undefined,
        });
        await fetchPatients();
      } else {
        const errData = await response.json().catch(() => ({}));
        setErrorMsg(errData.detail || 'Failed to add patient.');
      }
    } catch (err) {
      setErrorMsg('Error connecting to server.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRemovePatient = async (patientId: string, patientName: string) => {
    if (!window.confirm(`Are you sure you want to remove ${patientName} from your assigned caseload? Patient records will be preserved.`)) {
      return;
    }
    try {
      const response = await fetch(`/api/v1/asha/${user?.asha_worker_id}/patients/${patientId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        setSuccessMsg(`Patient ${patientName} successfully unassigned.`);
        await fetchPatients();
      }
    } catch (err) {
      console.error('Failed to unassign patient:', err);
    }
  };

  const filteredPatients = patients.filter(
    (p) =>
      p.full_name?.toLowerCase().includes(search.toLowerCase()) ||
      p.mrn?.toLowerCase().includes(search.toLowerCase()) ||
      p.village?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-4 space-y-6">
      {/* Header Actions */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-white">Assigned Patient Roster</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Manage your post-discharge patients, view details, and register new patients into PostgreSQL.
          </p>
        </div>
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
            <Input
              placeholder="Search patients..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          <Button
            onClick={() => setShowAddModal(true)}
            className="bg-teal-700 hover:bg-teal-600 text-white font-semibold flex items-center gap-2 px-4 py-2.5 rounded-xl whitespace-nowrap"
          >
            <UserPlus className="w-4 h-4" />
            <span>Add Patient</span>
          </Button>
        </div>
      </div>

      {/* Notifications */}
      {successMsg && (
        <div className="p-4 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-xl flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          <span>{successMsg}</span>
        </div>
      )}
      {errorMsg && (
        <div className="p-4 bg-red-50 text-red-800 border border-red-200 rounded-xl flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Patient Grid */}
      {loading ? (
        <div className="flex justify-center items-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600" />
        </div>
      ) : filteredPatients.length === 0 ? (
        <Card className="p-12 text-center">
          <p className="text-slate-500 dark:text-slate-400">No assigned patients found.</p>
        </Card>
      ) : (
        <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
          {filteredPatients.map((patient) => (
            <Card key={patient.id} className="p-5 flex flex-col justify-between hover:shadow-md transition-shadow">
              <div>
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-bold text-slate-900 text-lg">{patient.full_name}</h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      MRN: {patient.mrn} {patient.age ? `· ${patient.age} yrs` : ''}
                    </p>
                  </div>
                  <Badge variant={patient.risk_level === 'critical' ? 'danger' : patient.risk_level === 'warning' ? 'warning' : 'success'}>
                    {patient.risk_level}
                  </Badge>
                </div>

                <div className="space-y-1 text-sm text-slate-600 dark:text-slate-300 mb-4">
                  <p><span className="text-slate-400">Village:</span> {patient.village || 'N/A'}</p>
                  <p><span className="text-slate-400">Phone:</span> {patient.phone}</p>
                  {patient.last_checkin && (
                    <p className="text-xs text-slate-500 mt-2">
                      Last Check-in: {new Date(patient.last_checkin).toLocaleDateString()}
                    </p>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-slate-100 dark:border-slate-800 mt-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleRemovePatient(patient.id, patient.full_name)}
                  className="text-red-600 border-red-200 hover:bg-red-50 text-xs flex items-center gap-1"
                >
                  <UserX className="w-3.5 h-3.5" />
                  <span>Unassign</span>
                </Button>

                <Button
                  size="sm"
                  onClick={() => navigate(`/asha/patients/${patient.id}`)}
                  className="bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold"
                >
                  View Profile
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Add Patient Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex justify-center items-center p-4 overflow-y-auto">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl my-8">
            <div className="flex justify-between items-center pb-4 border-b border-slate-200 dark:border-slate-800 mb-4">
              <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-teal-600" />
                <span>Add & Register Patient</span>
              </h2>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-slate-600 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddPatient} className="space-y-4 text-sm">
              <div className="bg-teal-50/60 dark:bg-teal-950/40 p-3.5 rounded-xl border border-teal-200/80 dark:border-teal-800/60 mb-2">
                <label className="block text-xs font-bold text-teal-900 dark:text-teal-200 mb-1">
                  Select Saved Patient to Update / Re-assign (Optional)
                </label>
                <select
                  value={formData.patient_id}
                  onChange={(e) => handleSelectExisting(e.target.value)}
                  className="w-full px-3 py-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700 text-xs font-medium"
                >
                  <option value="">-- Create New Patient Record --</option>
                  {patients.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.full_name} ({p.phone || p.mrn || 'No Phone'})
                    </option>
                  ))}
                </select>
                <p className="text-[11px] text-teal-700 dark:text-teal-400 mt-1">
                  Choosing an existing patient populates their saved details so you can update their record or log new symptoms.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Full Name *</label>
                  <Input name="full_name" required value={formData.full_name} onChange={handleInputChange} placeholder="e.g. Rajesh Kumar" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Phone Number *</label>
                  <Input name="phone" required value={formData.phone} onChange={handleInputChange} placeholder="e.g. +91-9876543210" />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Age</label>
                  <Input name="age" type="number" value={formData.age} onChange={handleInputChange} placeholder="e.g. 58" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Gender</label>
                  <select name="gender" value={formData.gender} onChange={handleInputChange} className="w-full px-3 py-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700">
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Patient Login Email / Username</label>
                  <Input name="email" value={formData.email} onChange={handleInputChange} placeholder="Optional (auto-generated if empty)" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Patient Password</label>
                  <Input name="password" type="password" value={formData.password} onChange={handleInputChange} placeholder="Password for login" />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Condition / Medical Diagnosis</label>
                <Input name="condition" value={formData.condition} onChange={handleInputChange} placeholder="e.g. Post-cardiac surgery recovery" />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Current Symptoms</label>
                <textarea
                  name="symptoms"
                  rows={2}
                  value={formData.symptoms}
                  onChange={handleInputChange}
                  placeholder="e.g. Mild shortness of breath, fatigue"
                  className="w-full p-2.5 border rounded-xl dark:bg-slate-800 dark:border-slate-700"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Address</label>
                  <Input name="address" value={formData.address} onChange={handleInputChange} placeholder="Street / House No." />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Village</label>
                  <Input name="village" value={formData.village} onChange={handleInputChange} placeholder="Village name" />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">District</label>
                  <Input name="district" value={formData.district} onChange={handleInputChange} placeholder="District" />
                </div>
              </div>

              {/* Map Location Selector */}
              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-teal-600" />
                    <span>Map Location Coordinates (Click map to pin)</span>
                  </label>
                  <button type="button" onClick={handleGeocode} className="text-xs text-teal-600 hover:underline">
                    Find from address
                  </button>
                </div>

                <PatientMap
                  markers={[
                    {
                      id: 'new-pin',
                      lat: Number(formData.latitude) || 12.9716,
                      lng: Number(formData.longitude) || 77.5946,
                      label: formData.full_name || 'New Patient Location',
                      color: '#0d9488',
                    },
                  ]}
                  height="180px"
                  onMapClick={(lat, lng) => {
                    setFormData((prev) => ({
                      ...prev,
                      latitude: parseFloat(lat.toFixed(6)),
                      longitude: parseFloat(lng.toFixed(6)),
                    }));
                  }}
                />

                <div className="grid grid-cols-2 gap-3 mt-2">
                  <div>
                    <label className="block text-xs text-slate-500">Latitude</label>
                    <Input name="latitude" type="number" step="any" value={formData.latitude} onChange={handleInputChange} />
                  </div>
                  <div>
                    <label className="block text-xs text-slate-500">Longitude</label>
                    <Input name="longitude" type="number" step="any" value={formData.longitude} onChange={handleInputChange} />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-200 dark:border-slate-800">
                <Button type="button" variant="outline" onClick={() => setShowAddModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={isSubmitting} className="bg-teal-700 hover:bg-teal-600 text-white font-semibold">
                  {isSubmitting ? 'Saving to Database...' : 'Register Patient'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AshaPatients;

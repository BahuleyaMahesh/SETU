import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from '../../../shared/components/Card';
import { Badge } from '../../../shared/components/Badge';
import { Button } from '../../../shared/components/Button';
import { Input } from '../../../shared/components/Input';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../app/auth/AuthProvider';
import { UserPlus, AlertCircle, CheckCircle2, MapPin } from 'lucide-react';
import { PatientMap } from '../../maps/components/PatientMap';
import { PatientMedicationsPanel } from '../../../shared/components/PatientMedicationsPanel';
import { ScheduleCallPanel } from '../../../shared/components/ScheduleCallPanel';
import { PatientContactPanel } from '../../../shared/components/PatientContactPanel';
import { RiskHistoryTimeline } from '../../../shared/components/RiskHistoryTimeline';
import { CallHistoryPanel } from '../../../shared/components/CallHistoryPanel';

interface PatientItem {
  id: string;
  mrn: string;
  full_name: string;
  age?: number;
  gender?: string;
  phone?: string;
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

export const HospitalPatients: React.FC = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [patients, setPatients] = useState<PatientItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState<string>('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const [formData, setFormData] = useState({
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

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    fetchPatients();
    if (window.location.search.includes('add=true')) {
      setShowAddModal(true);
    }
  }, [token, riskFilter]);

  const fetchPatients = async () => {
    setLoading(true);
    try {
      const url = riskFilter !== 'all' ? `/api/v1/patients?risk_level=${riskFilter}` : `/api/v1/patients`;
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setPatients(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error('Failed to fetch hospital patients:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

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

  const handleAddPatient = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');
    if (!formData.full_name || !formData.phone) {
      setErrorMsg('Name and Phone Number are required.');
      return;
    }
    setIsSubmitting(true);
    try {
      // No {asha_id} in the URL — the backend resolves hospital/ASHA scope
      // from the authenticated user's own JWT (POST-only route, no GET
      // sibling takes a path param here, unlike /asha/{asha_id}/patients).
      const response = await fetch(`/api/v1/asha/patients`, {
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
        setSuccessMsg(formData.patient_id ? 'Patient details updated successfully!' : 'Patient successfully registered!');
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
          latitude: 12.9716,
          longitude: 77.5946,
        });
        await fetchPatients();
      } else {
        const errData = await response.json().catch(() => ({}));
        setErrorMsg(errData.detail || 'Failed to save patient details.');
      }
    } catch (err) {
      setErrorMsg('Error connecting to server.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredPatients = patients.filter((p) => {
    const matchesSearch =
      p.full_name?.toLowerCase().includes(search.toLowerCase()) ||
      p.mrn?.toLowerCase().includes(search.toLowerCase()) ||
      p.village?.toLowerCase().includes(search.toLowerCase());
    return matchesSearch;
  });

  return (
    <div className="p-4 space-y-4">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white">Hospital Patient Directory</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">Post-discharge patient cohort active in PostgreSQL database.</p>
        </div>
        <div className="flex flex-wrap sm:flex-nowrap gap-2 w-full sm:w-auto">
          <Input
            placeholder="Search name, MRN..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full sm:w-64"
          />
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="px-3 py-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700 text-sm font-medium"
          >
            <option value="all">All Risks</option>
            <option value="normal">Normal</option>
            <option value="warning">Warning</option>
            <option value="critical">Critical</option>
          </select>
          <Button
            onClick={() => setShowAddModal(true)}
            className="bg-sky-600 hover:bg-sky-500 text-white font-semibold flex items-center gap-2 px-4 py-2 rounded-xl whitespace-nowrap"
          >
            <UserPlus className="w-4 h-4" />
            <span>Add Patient</span>
          </Button>
        </div>
      </div>

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

      {loading ? (
        <div className="flex justify-center items-center py-16">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600" />
        </div>
      ) : filteredPatients.length === 0 ? (
        <Card className="p-12 text-center text-slate-500">No patients found.</Card>
      ) : (
        <div className="grid gap-4">
          {filteredPatients.map((patient) => (
            <Card key={patient.id} className="p-5">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-bold text-slate-900 text-lg">{patient.full_name}</h3>
                  <p className="text-sm text-slate-500 mt-0.5">
                    {patient.age ? `${patient.age} years | ` : ''}MRN: {patient.mrn} | Village: {patient.village || 'N/A'}
                  </p>
                </div>
                <Badge variant={patient.risk_level === 'critical' ? 'danger' : patient.risk_level === 'warning' ? 'warning' : 'success'}>
                  {patient.risk_level}
                </Badge>
              </div>
              <div className="flex justify-between items-center mt-4 pt-3 border-t border-slate-100 dark:border-slate-800">
                <span className="text-xs text-slate-500">
                  {patient.last_checkin ? `Last check-in: ${new Date(patient.last_checkin).toLocaleDateString()}` : 'No check-ins yet'}
                </span>
                <Link to={`/hospital/patients/${patient.id}`}>
                  <Button size="sm" variant="outline" className="text-xs font-semibold">
                    View Details
                  </Button>
                </Link>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Add / Update Patient Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex justify-center items-center p-4 overflow-y-auto">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl my-8">
            <div className="flex justify-between items-center pb-4 border-b border-slate-200 dark:border-slate-800 mb-4">
              <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-sky-600" />
                <span>Add / Update Patient Record</span>
              </h2>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-slate-600 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddPatient} className="space-y-4 text-sm">
              <div className="bg-sky-50/60 dark:bg-sky-950/40 p-3.5 rounded-xl border border-sky-200/80 dark:border-sky-800/60 mb-2">
                <label className="block text-xs font-bold text-sky-900 dark:text-sky-200 mb-1">
                  Select Saved Patient to Edit / Update Details (Optional)
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
                <p className="text-[11px] text-sky-700 dark:text-sky-400 mt-1">
                  Choosing an existing patient populates their saved details so you can update their medical record.
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
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Map Location Coordinates
                </label>
                <PatientMap
                  markers={[
                    {
                      id: 'new-pin',
                      lat: Number(formData.latitude) || 12.9716,
                      lng: Number(formData.longitude) || 77.5946,
                      label: formData.full_name || 'Patient Location',
                      color: '#0284c7',
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
                <Button type="submit" disabled={isSubmitting} className="bg-sky-600 hover:bg-sky-500 text-white font-semibold">
                  {isSubmitting ? 'Saving to Database...' : formData.patient_id ? 'Update Patient Details' : 'Register Patient'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export const HospitalPatientDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [patient, setPatient] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id || !token) {
      setLoading(false);
      return;
    }
    fetch(`/api/v1/patients/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        setPatient(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching patient details:', err);
        setLoading(false);
      });
  }, [id, token]);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-16">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600" />
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="p-8 text-center">
        <p className="text-slate-500">Patient record not found.</p>
        <Button onClick={() => navigate('/hospital/patients')} className="mt-4" variant="outline">
          Back to Directory
        </Button>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center gap-4 mb-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/hospital/patients')}>
          ← Back
        </Button>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Patient: {patient.full_name}</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <Card className="p-6">
            <h2 className="text-lg font-bold text-slate-900 mb-4">Patient Profile</h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-xs text-slate-400 font-semibold uppercase">MRN</span>
                <p className="font-bold text-slate-800">{patient.mrn}</p>
              </div>
              <div>
                <span className="text-xs text-slate-400 font-semibold uppercase">Age</span>
                <p className="font-bold text-slate-800">{patient.age || 'N/A'}</p>
              </div>
              <div>
                <span className="text-xs text-slate-400 font-semibold uppercase">Gender</span>
                <p className="font-bold text-slate-800">{patient.gender || 'N/A'}</p>
              </div>
              <div>
                <span className="text-xs text-slate-400 font-semibold uppercase">Phone</span>
                <p className="font-bold text-slate-800">{patient.phone}</p>
              </div>
              <div>
                <span className="text-xs text-slate-400 font-semibold uppercase">Village / District</span>
                <p className="font-bold text-slate-800">{patient.village}, {patient.district}</p>
              </div>
              <div>
                <span className="text-xs text-slate-400 font-semibold uppercase">State / Pincode</span>
                <p className="font-bold text-slate-800">{patient.state} {patient.pincode}</p>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <PatientContactPanel
              patientId={patient.id}
              phone={patient.phone}
              village={patient.village}
              district={patient.district}
              state={patient.state}
              address={patient.address}
              latitude={patient.latitude}
              longitude={patient.longitude}
            />
          </Card>

          {/* Consolidated Clinical View for Hospital */}
          <Card className="p-6">
            <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-3 mb-4">
              <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <span>🩺 Consolidated Clinical View</span>
              </h2>
              <Badge variant={patient.risk_level === 'critical' ? 'danger' : patient.risk_level === 'warning' ? 'warning' : 'success'}>
                {patient.risk_level?.toUpperCase() || 'NORMAL'} RISK
              </Badge>
            </div>

            {/* Combined Symptoms & Observations */}
            <div className="space-y-4">
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Combined Symptoms & Observations</h3>
                {patient.combined_symptoms && patient.combined_symptoms.length > 0 ? (
                  <div className="space-y-3">
                    {patient.combined_symptoms.map((sym: any, idx: number) => (
                      <div key={idx} className="p-3 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-xl space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="font-bold text-slate-900 dark:text-white text-sm">
                            {sym.symptom_name || sym.symptom_key}
                          </span>
                          <span className="text-xs text-slate-500 font-medium">
                            {sym.observations?.length || 0} observation(s)
                          </span>
                        </div>
                        <div className="space-y-1 pl-2 border-l-2 border-teal-500">
                          {sym.observations?.map((obs: any, oIdx: number) => (
                            <div key={oIdx} className="text-xs flex items-start justify-between gap-2 py-0.5">
                              <div>
                                <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider mr-2 ${
                                  obs.reporter === 'asha' ? 'bg-teal-100 text-teal-800' : 'bg-sky-100 text-sky-800'
                                }`}>
                                  {obs.reporter}
                                </span>
                                <span className="text-slate-700 dark:text-slate-300 font-medium">"{obs.original_wording}"</span>
                              </div>
                              <span className="text-slate-400 text-[11px] whitespace-nowrap">
                                {new Date(obs.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic">No symptoms reported yet.</p>
                )}
              </div>

              {/* Risk & Symptom Timeline — the improvements-over-time log */}
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Symptom & Risk Timeline</h3>
                <RiskHistoryTimeline history={patient.risk_history} />
              </div>

              {/* Deterministic Risk Reasons */}
              {patient.latest_risk?.risk_reasons && patient.latest_risk.risk_reasons.length > 0 && (
                <div className="p-4 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-xl">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-amber-800 dark:text-amber-300 mb-2">Deterministic Risk Reasons</h3>
                  <ul className="list-disc list-inside text-xs text-amber-900 dark:text-amber-200 space-y-1 font-medium">
                    {patient.latest_risk.risk_reasons.map((r: string, i: number) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </Card>

          {patient.asha_worker && (
            <Card className="p-6">
              <h2 className="text-lg font-bold text-slate-900 mb-3">Assigned ASHA Worker</h2>
              <div className="flex items-center gap-4 bg-teal-50 border border-teal-200 p-4 rounded-xl">
                <div className="w-10 h-10 bg-teal-600 text-white font-bold rounded-lg flex items-center justify-center">
                  {patient.asha_worker.full_name?.[0] || 'A'}
                </div>
                <div>
                  <p className="font-bold text-slate-900">{patient.asha_worker.full_name}</p>
                  <p className="text-xs text-teal-700">Phone: {patient.asha_worker.phone} · District: {patient.asha_worker.district}</p>
                </div>
              </div>
            </Card>
          )}

          <Card className="p-6">
            <CallHistoryPanel calls={patient.calls} />
          </Card>

          <Card className="p-6">
            <ScheduleCallPanel patientId={patient.id} />
          </Card>

          <Card className="p-6">
            <PatientMedicationsPanel patientId={patient.id} />
          </Card>
        </div>

        <div className="space-y-4">
          <Card className="p-6">
            <h2 className="text-lg font-bold text-slate-900 mb-4">Current Risk Level</h2>
            <div className="flex items-center gap-3">
              <Badge variant={patient.risk_level === 'critical' ? 'danger' : patient.risk_level === 'warning' ? 'warning' : 'success'}>
                {patient.risk_level.toUpperCase()}
              </Badge>
            </div>
          </Card>

          <Card className="p-6">
            <h2 className="text-lg font-bold text-slate-900 mb-4">Quick Actions</h2>
            <div className="space-y-2">
              <Button className="w-full" variant="outline" onClick={() => navigate('/hospital/alerts')}>
                Create Clinical Alert
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default HospitalPatients;

import React, { useEffect, useState } from 'react';

interface PatientDetailProps {
  patientId: string;
}

interface Patient {
  id: string;
  mrn?: string;
  full_name: string;
  phone: string;
  age?: number;
  gender?: string;
  address?: string;
  village?: string;
  district?: string;
  state?: string;
  pincode?: string;
  latitude?: number;
  longitude?: number;
  risk_level?: string;
  last_checkin?: string;
  asha_worker?: {
    full_name?: string;
    phone?: string;
    district?: string;
  };
}

export const PatientDetail: React.FC<PatientDetailProps> = ({ patientId }) => {
  const [patient, setPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(true);
  const [showEditModal, setShowEditModal] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState('');

  const [editForm, setEditForm] = useState({
    full_name: '',
    phone: '',
    age: '',
    gender: 'Male',
    address: '',
    village: '',
    district: '',
    state: 'Karnataka',
    pincode: '',
    condition: '',
    symptoms: '',
  });

  const fetchPatientDetails = () => {
    const token = localStorage.getItem('token');
    setLoading(true);
    fetch(`/api/v1/patients/${patientId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((d) => {
        setPatient(d);
        if (d) {
          setEditForm({
            full_name: d.full_name || '',
            phone: d.phone || '',
            age: d.age ? String(d.age) : '',
            gender: d.gender || 'Male',
            address: d.address || '',
            village: d.village || '',
            district: d.district || '',
            state: d.state || 'Karnataka',
            pincode: d.pincode || '',
            condition: '',
            symptoms: '',
          });
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  useEffect(() => {
    fetchPatientDetails();
  }, [patientId]);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setMessage('');
    const token = localStorage.getItem('token');
    try {
      const userStr = localStorage.getItem('user');
      const userObj = userStr ? JSON.parse(userStr) : null;
      const ashaId = userObj?.asha_worker_id || '00000000-0000-0000-0000-000000000000';

      const response = await fetch(`/api/v1/patients/${patientId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          ...editForm,
          age: editForm.age ? parseInt(editForm.age, 10) : undefined,
        }),
      });

      if (response.ok) {
        setMessage('Patient details updated successfully!');
        setShowEditModal(false);
        fetchPatientDetails();
      } else {
        const errData = await response.json().catch(() => ({}));
        setMessage(errData.detail || 'Failed to update patient details.');
      }
    } catch (err) {
      setMessage('Error updating patient details.');
    } finally {
      setIsSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600" />
      </div>
    );
  }

  if (!patient) {
    return <div className="text-center p-8 text-slate-500">Patient record not found.</div>;
  }

  return (
    <div className="space-y-4">
      {message && (
        <div className="p-3 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-xl text-sm font-medium">
          {message}
        </div>
      )}

      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">{patient.full_name}</h2>
          <p className="text-xs text-slate-500 mt-1">MRN: {patient.mrn || 'N/A'}</p>
        </div>
        <button
          onClick={() => setShowEditModal(true)}
          className="bg-teal-700 hover:bg-teal-600 text-white text-xs font-semibold px-4 py-2 rounded-xl transition-colors"
        >
          Edit / Update Details
        </button>
      </div>

      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-4">
        <h3 className="text-lg font-bold text-slate-900 dark:text-white">Patient Profile</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-xs text-slate-400 font-semibold uppercase">Phone</span>
            <p className="font-bold text-slate-800 dark:text-slate-200">{patient.phone}</p>
          </div>
          <div>
            <span className="text-xs text-slate-400 font-semibold uppercase">Age</span>
            <p className="font-bold text-slate-800 dark:text-slate-200">{patient.age ? `${patient.age} years` : 'N/A'}</p>
          </div>
          <div>
            <span className="text-xs text-slate-400 font-semibold uppercase">Gender</span>
            <p className="font-bold text-slate-800 dark:text-slate-200">{patient.gender || 'N/A'}</p>
          </div>
          <div>
            <span className="text-xs text-slate-400 font-semibold uppercase">Village</span>
            <p className="font-bold text-slate-800 dark:text-slate-200">{patient.village || 'N/A'}</p>
          </div>
          <div>
            <span className="text-xs text-slate-400 font-semibold uppercase">District</span>
            <p className="font-bold text-slate-800 dark:text-slate-200">{patient.district || 'N/A'}</p>
          </div>
          <div>
            <span className="text-xs text-slate-400 font-semibold uppercase">State</span>
            <p className="font-bold text-slate-800 dark:text-slate-200">{patient.state || 'Karnataka'}</p>
          </div>
          {patient.address && (
            <div className="col-span-2">
              <span className="text-xs text-slate-400 font-semibold uppercase">Address</span>
              <p className="font-bold text-slate-800 dark:text-slate-200">{patient.address}</p>
            </div>
          )}
          {patient.risk_level && (
            <div>
              <span className="text-xs text-slate-400 font-semibold uppercase">Risk Status</span>
              <p className="font-bold capitalize text-teal-700 dark:text-teal-400">{patient.risk_level}</p>
            </div>
          )}
          {patient.last_checkin && (
            <div className="col-span-2 sm:col-span-3">
              <span className="text-xs text-slate-400 font-semibold uppercase">Last Check-in</span>
              <p className="font-bold text-slate-800 dark:text-slate-200">{new Date(patient.last_checkin).toLocaleString()}</p>
            </div>
          )}
        </div>
      </div>

      {/* Clinical Overview: Consolidated Symptoms, Risk Reasons & History */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm space-y-6">
        <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-800 pb-3">
          <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <span>🩺 Consolidated Clinical View</span>
          </h3>
          <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${
            patient.risk_level === 'critical' ? 'bg-red-100 text-red-700' :
            patient.risk_level === 'warning' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'
          }`}>
            {patient.risk_level || 'normal'} Risk
          </span>
        </div>

        {/* Combined Symptoms & Observations */}
        <div>
          <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">Combined Symptoms & Observations</h4>
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

        {/* Active Risk Factors & Reasons */}
        {patient.latest_risk?.risk_reasons && patient.latest_risk.risk_reasons.length > 0 && (
          <div className="p-4 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-xl">
            <h4 className="text-xs font-bold uppercase tracking-wider text-amber-800 dark:text-amber-300 mb-2">Deterministic Risk Reasons</h4>
            <ul className="list-disc list-inside text-xs text-amber-900 dark:text-amber-200 space-y-1 font-medium">
              {patient.latest_risk.risk_reasons.map((r: string, i: number) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Active Alerts */}
        {patient.alerts && patient.alerts.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">Active & Recent Alerts</h4>
            <div className="space-y-2">
              {patient.alerts.slice(0, 5).map((alt: any) => (
                <div key={alt.id} className="p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-xl flex justify-between items-center text-xs">
                  <div>
                    <span className="font-bold text-red-900 dark:text-red-200">{alt.title}</span>
                    <p className="text-red-700 dark:text-red-300 mt-0.5">{alt.description}</p>
                  </div>
                  <span className="text-slate-500 text-[11px]">
                    {new Date(alt.created_at).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Edit Modal */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex justify-center items-center p-4 overflow-y-auto">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl my-8">
            <div className="flex justify-between items-center pb-4 border-b border-slate-200 dark:border-slate-800 mb-4">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">Edit Patient Details</h3>
              <button onClick={() => setShowEditModal(false)} className="text-slate-400 hover:text-slate-600 font-bold">
                ✕
              </button>
            </div>

            <form onSubmit={handleUpdate} className="space-y-4 text-sm">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold mb-1">Full Name</label>
                  <input
                    className="w-full p-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700"
                    value={editForm.full_name}
                    onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1">Phone</label>
                  <input
                    className="w-full p-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700"
                    value={editForm.phone}
                    onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1">Age</label>
                  <input
                    type="number"
                    className="w-full p-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700"
                    value={editForm.age}
                    onChange={(e) => setEditForm({ ...editForm, age: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1">Gender</label>
                  <select
                    className="w-full p-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700"
                    value={editForm.gender}
                    onChange={(e) => setEditForm({ ...editForm, gender: e.target.value })}
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1">Village</label>
                  <input
                    className="w-full p-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700"
                    value={editForm.village}
                    onChange={(e) => setEditForm({ ...editForm, village: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold mb-1">District</label>
                  <input
                    className="w-full p-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700"
                    value={editForm.district}
                    onChange={(e) => setEditForm({ ...editForm, district: e.target.value })}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold mb-1">Address</label>
                <input
                  className="w-full p-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700"
                  value={editForm.address}
                  onChange={(e) => setEditForm({ ...editForm, address: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold mb-1">Condition / Diagnosis (Optional)</label>
                <input
                  className="w-full p-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700"
                  value={editForm.condition}
                  onChange={(e) => setEditForm({ ...editForm, condition: e.target.value })}
                  placeholder="e.g. Recovering from pneumonia"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold mb-1">New Symptoms / Notes (Optional)</label>
                <textarea
                  rows={2}
                  className="w-full p-2 border rounded-xl dark:bg-slate-800 dark:border-slate-700"
                  value={editForm.symptoms}
                  onChange={(e) => setEditForm({ ...editForm, symptoms: e.target.value })}
                  placeholder="Log symptoms or visit notes"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-200 dark:border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowEditModal(false)}
                  className="px-4 py-2 border rounded-xl text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSaving}
                  className="px-4 py-2 bg-teal-700 text-white rounded-xl font-semibold hover:bg-teal-600"
                >
                  {isSaving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default PatientDetail;

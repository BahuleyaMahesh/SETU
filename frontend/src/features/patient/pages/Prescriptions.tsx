import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../app/auth/AuthProvider';
import { Card, CardHeader, CardContent } from '../../../shared/components/Card';
import { Badge } from '../../../shared/components/Badge';
import { Button } from '../../../shared/components/Button';
import { FileText, Upload, CheckCircle2, Pill, Clock, Sparkles } from 'lucide-react';
import { MedicationRemindersPanel } from '../../../shared/components/MedicationRemindersPanel';

export const PatientPrescriptions: React.FC = () => {
  const { user, token } = useAuth();
  const [prescriptions, setPrescriptions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploadStage, setUploadStage] = useState<'idle' | 'uploading' | 'analyzing'>('idle');
  const [uploadError, setUploadError] = useState('');
  // Bumped after an upload so the reminders panel refetches and shows the
  // reminders the new prescription just auto-created.
  const [remindersVersion, setRemindersVersion] = useState(0);

  useEffect(() => {
    fetchPrescriptions();
  }, [token, user?.patient_id]);

  const fetchPrescriptions = async () => {
    if (!user?.patient_id) {
      setLoading(false);
      return;
    }
    try {
      const response = await fetch(`/api/v1/prescriptions/patient/${user.patient_id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setPrescriptions(data);
      }
    } catch (error) {
      console.error('Error fetching prescriptions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !user?.patient_id) return;

    setUploadError('');
    setUploadStage('uploading');
    const formData = new FormData();
    formData.append('file', file);
    formData.append('patient_id', user.patient_id);

    try {
      const uploadRes = await fetch('/api/v1/documents/upload', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!uploadRes.ok) {
        throw new Error('Upload failed');
      }
      const document = await uploadRes.json();

      setUploadStage('analyzing');
      const extractRes = await fetch(`/api/v1/prescriptions/from-document/${document.id}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!extractRes.ok) {
        const err = await extractRes.json().catch(() => ({}));
        throw new Error(err.detail || 'Could not read medications from this image');
      }

      await fetchPrescriptions();
      setRemindersVersion((v) => v + 1);
    } catch (error: any) {
      setUploadError(error.message || 'Upload failed. Please try again.');
    } finally {
      setUploadStage('idle');
      e.target.value = '';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-16">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <FileText className="w-5 h-5 text-sky-600" />
            <span>Prescriptions & Medications</span>
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">Uploaded discharge notes and AI extracted medication records.</p>
        </div>

        <label className={`inline-flex items-center justify-center gap-2 bg-sky-600 hover:bg-sky-500 text-white font-semibold text-sm px-4 py-2.5 rounded-xl cursor-pointer shadow-md shadow-sky-600/20 transition-all ${uploadStage !== 'idle' ? 'opacity-70 pointer-events-none' : ''}`}>
          <Upload className="w-4 h-4" />
          <span>
            {uploadStage === 'uploading' ? 'Uploading...' : uploadStage === 'analyzing' ? 'Reading with AI...' : 'Upload Prescription'}
          </span>
          <input type="file" accept="image/*" onChange={handleFileUpload} className="hidden" disabled={uploadStage !== 'idle'} />
        </label>
      </div>

      {uploadError && (
        <div className="p-3.5 bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl font-medium">
          {uploadError}
        </div>
      )}

      {prescriptions.length === 0 ? (
        <Card className="p-8 text-center bg-slate-50 border border-slate-200 rounded-2xl">
          <Pill className="w-10 h-10 text-slate-400 mx-auto mb-3" />
          <h3 className="font-bold text-slate-700 text-base">No Prescriptions Uploaded</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Upload your hospital discharge slip or prescription image to automatically extract medication reminders.
          </p>
        </Card>
      ) : (
        <div className="grid gap-4">
          {prescriptions.map((prescription) => (
            <Card key={prescription.id} className="p-5 border-slate-200 shadow-sm hover:border-slate-300 transition-all">
              <div className="flex justify-between items-start border-b border-slate-100 pb-3 mb-4">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-teal-600" />
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Uploaded: {new Date(prescription.created_at || Date.now()).toLocaleDateString()}
                  </span>
                </div>
                <Badge variant={prescription.status === 'verified' ? 'success' : 'warning'}>
                  {prescription.status || 'verified'}
                </Badge>
              </div>

              <div className="space-y-2.5">
                {(prescription.medications || []).map((med: any, index: number) => (
                  <div key={index} className="bg-slate-50 border border-slate-200/80 p-3.5 rounded-xl flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-sky-50 text-sky-600 rounded-lg">
                        <Pill className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="font-bold text-slate-900 text-sm">{med.name || med.medication_name}</div>
                        <div className="text-xs text-slate-500 mt-0.5">
                          Dosage: {med.dosage} • Frequency: {med.frequency}
                        </div>
                      </div>
                    </div>
                    {med.verified && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </div>
      )}

      {user?.patient_id && (
        <Card className="p-5 border-slate-200 rounded-2xl">
          <MedicationRemindersPanel patientId={user.patient_id} refreshKey={remindersVersion} />
        </Card>
      )}
    </div>
  );
};

export default PatientPrescriptions;

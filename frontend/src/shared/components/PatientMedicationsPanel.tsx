import React, { useEffect, useState } from 'react';
import { useAuth } from '../../app/auth/AuthProvider';
import { Card } from './Card';
import { Badge } from './Badge';
import { FileText, Upload, Pill, Sparkles } from 'lucide-react';
import { MedicationRemindersPanel } from './MedicationRemindersPanel';

interface PatientMedicationsPanelProps {
  /** The patient this panel is for — NOT necessarily the logged-in user.
   * Lets ASHA/hospital staff upload a prescription and see reminders for a
   * patient in their care who may have no login/email of their own (rural
   * patients on a basic phone, no smartphone) — same upload + auto-reminder
   * pipeline as the patient's own self-service Prescriptions page, just
   * usable on someone else's behalf. */
  patientId: string;
}

export const PatientMedicationsPanel: React.FC<PatientMedicationsPanelProps> = ({ patientId }) => {
  const { token } = useAuth();
  const [prescriptions, setPrescriptions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploadStage, setUploadStage] = useState<'idle' | 'uploading' | 'analyzing'>('idle');
  const [uploadError, setUploadError] = useState('');
  // Bumped after an upload so the reminders panel refetches and shows the
  // reminders the prescription just auto-created.
  const [remindersVersion, setRemindersVersion] = useState(0);

  useEffect(() => {
    fetchPrescriptions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, patientId]);

  const fetchPrescriptions = async () => {
    if (!patientId) {
      setLoading(false);
      return;
    }
    try {
      const res = await fetch(`/api/v1/prescriptions/patient/${patientId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) setPrescriptions(await res.json());
    } catch (error) {
      console.error('Error fetching prescriptions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !patientId) return;

    setUploadError('');
    setUploadStage('uploading');
    const formData = new FormData();
    formData.append('file', file);
    formData.append('patient_id', patientId);

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
      <div className="flex justify-center items-center py-8">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-sky-600" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-3">
        <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
          <FileText className="w-4 h-4 text-sky-600" />
          Prescriptions & Medication Reminders
        </h3>
        <label className={`inline-flex items-center justify-center gap-2 bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs px-3 py-2 rounded-lg cursor-pointer transition-all ${uploadStage !== 'idle' ? 'opacity-70 pointer-events-none' : ''}`}>
          <Upload className="w-3.5 h-3.5" />
          <span>
            {uploadStage === 'uploading' ? 'Uploading...' : uploadStage === 'analyzing' ? 'Reading with AI...' : 'Upload Prescription'}
          </span>
          <input type="file" accept="image/*" onChange={handleFileUpload} className="hidden" disabled={uploadStage !== 'idle'} />
        </label>
      </div>

      {uploadError && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg font-medium">
          {uploadError}
        </div>
      )}

      {prescriptions.length === 0 ? (
        <Card className="p-6 text-center bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-xl">
          <Pill className="w-8 h-8 text-slate-400 mx-auto mb-2" />
          <p className="text-xs text-slate-500 dark:text-slate-400">
            No prescriptions uploaded yet. Upload a photo to auto-extract medications and schedule reminders.
          </p>
        </Card>
      ) : (
        <div className="space-y-3">
          {prescriptions.map((prescription: any) => (
            <Card key={prescription.id} className="p-4 border-slate-200 dark:border-slate-700 rounded-xl">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-teal-600" />
                  {new Date(prescription.created_at || Date.now()).toLocaleDateString()}
                </span>
                <Badge variant={prescription.status === 'verified' ? 'success' : 'warning'}>
                  {prescription.status || 'verified'}
                </Badge>
              </div>
              <div className="space-y-1.5">
                {(prescription.medications || []).map((med: any, idx: number) => (
                  <div key={idx} className="text-xs text-slate-700 dark:text-slate-300">
                    <span className="font-semibold">{med.name || med.medication_name}</span>
                    {' — '}{med.dosage} · {med.frequency}
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </div>
      )}

      <MedicationRemindersPanel patientId={patientId} refreshKey={remindersVersion} />
    </div>
  );
};

export default PatientMedicationsPanel;

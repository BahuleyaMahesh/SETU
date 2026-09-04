import React, { useEffect, useState } from 'react';

interface PatientDetailProps {
  patientId: string;
}

interface Patient {
  id: string;
  full_name: string;
  phone: string;
  age?: number;
  risk_level?: string;
  last_checkin?: string;
  district?: string;
}

export const PatientDetail: React.FC<PatientDetailProps> = ({ patientId }) => {
  const [patient, setPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    fetch(`/api/v1/patients/${patientId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(d => { setPatient(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [patientId]);

  if (loading) {
    return <div className="flex justify-center p-8"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" /></div>;
  }

  if (!patient) {
    return <div className="text-center p-8 text-gray-500">Patient not found</div>;
  }

  return (
    <div className="bg-white rounded-xl shadow p-6 space-y-4">
      <h2 className="text-xl font-semibold text-gray-900">{patient.full_name}</h2>
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-gray-500">Phone</span>
          <p className="font-medium">{patient.phone}</p>
        </div>
        {patient.age && (
          <div>
            <span className="text-gray-500">Age</span>
            <p className="font-medium">{patient.age} years</p>
          </div>
        )}
        {patient.district && (
          <div>
            <span className="text-gray-500">District</span>
            <p className="font-medium">{patient.district}</p>
          </div>
        )}
        {patient.risk_level && (
          <div>
            <span className="text-gray-500">Risk Level</span>
            <p className="font-medium capitalize">{patient.risk_level}</p>
          </div>
        )}
        {patient.last_checkin && (
          <div className="col-span-2">
            <span className="text-gray-500">Last Check-in</span>
            <p className="font-medium">{new Date(patient.last_checkin).toLocaleString()}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default PatientDetail;

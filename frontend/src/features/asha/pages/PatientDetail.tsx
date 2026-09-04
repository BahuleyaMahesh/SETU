import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PatientDetail as AshaPatientDetailComponent } from '../components/PatientDetail';

export const AshaPatientDetail: React.FC = () => {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();

  if (!patientId) {
    return (
      <div className="p-4 text-center text-red-600">
        Patient ID missing. <button onClick={() => navigate('/asha/patients')} className="underline">Back to list</button>
      </div>
    );
  }

  return (
    <div className="p-4">
      <button onClick={() => navigate('/asha/patients')} className="mb-4 text-sm text-gray-600 hover:text-gray-900">
        &larr; Back to Patients
      </button>
      <AshaPatientDetailComponent patientId={patientId} />
    </div>
  );
};

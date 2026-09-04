import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../app/auth/AuthProvider';
import { Card, CardHeader, CardContent } from '../../../shared/components/Card';
import { Button } from '../../../shared/components/Button';
import { Input } from '../../../shared/components/Input';
import { Badge } from '../../../shared/components/Badge';

export const PatientProfile: React.FC = () => {
  const { user, token } = useAuth();
  const [patientData, setPatientData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    if (!token || !user?.patient_id) {
      setLoading(false);
      return;
    }
    fetch(`/api/v1/patients/${user.patient_id}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) setPatientData(data);
      })
      .catch((err) => console.error('Error fetching patient profile:', err))
      .finally(() => setLoading(false));
  }, [token, user?.patient_id]);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-16">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600" />
      </div>
    );
  }

  const name = patientData?.full_name || user?.full_name || 'Patient';
  const mrn = patientData?.mrn || 'N/A';
  const age = patientData?.age || 'N/A';
  const gender = patientData?.gender || 'N/A';
  const phone = patientData?.phone || user?.phone || 'N/A';
  const address = patientData?.address || 'N/A';
  const riskLevel = patientData?.risk_level || 'normal';

  return (
    <div className="p-4 space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-semibold">My Profile</h1>
      </div>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-medium">Personal Information</h2>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-gray-500">MRN</label>
              <div className="font-medium">{mrn}</div>
            </div>
            <div>
              <label className="text-sm text-gray-500">Name</label>
              <div className="font-medium">{name}</div>
            </div>
            <div>
              <label className="text-sm text-gray-500">Age</label>
              <div className="font-medium">{age}</div>
            </div>
            <div>
              <label className="text-sm text-gray-500">Gender</label>
              <div className="font-medium">{gender}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-medium">Contact Information</h2>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <label className="text-sm text-gray-500">Phone</label>
            <div className="font-medium">{phone}</div>
          </div>
          <div>
            <label className="text-sm text-gray-500">Address</label>
            <div className="font-medium">{address}</div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-medium">Health Status</h2>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-500 font-medium">Current Persisted Risk Level:</span>
            <Badge variant={riskLevel === 'critical' ? 'danger' : riskLevel === 'warning' ? 'warning' : 'success'}>
              {riskLevel.toUpperCase()}
            </Badge>
          </div>
          {patientData?.latest_risk?.risk_reasons && patientData.latest_risk.risk_reasons.length > 0 && (
            <div className="mt-3 p-3 bg-slate-50 rounded-lg text-xs text-slate-600">
              <span className="font-bold text-slate-700 block mb-1">Clinical Reasons:</span>
              <ul className="list-disc list-inside space-y-0.5">
                {patientData.latest_risk.risk_reasons.map((r: string, idx: number) => (
                  <li key={idx}>{r}</li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export const AshaProfile: React.FC = () => {
  const [profile, setProfile] = useState({
    name: 'Priya Sharma',
    ashaId: 'ASHA001',
    district: 'Bangalore',
    block: 'Whitefield',
    phone: '+91-98765-43210',
  });

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-semibold mb-4">ASHA Profile</h1>

      <Card>
        <CardContent className="space-y-3">
          <div>
            <label className="text-sm text-gray-500">Name</label>
            <div className="font-medium">{profile.name}</div>
          </div>
          <div>
            <label className="text-sm text-gray-500">ASHA ID</label>
            <div className="font-medium">{profile.ashaId}</div>
          </div>
          <div>
            <label className="text-sm text-gray-500">District</label>
            <div className="font-medium">{profile.district}</div>
          </div>
          <div>
            <label className="text-sm text-gray-500">Block</label>
            <div className="font-medium">{profile.block}</div>
          </div>
          <div>
            <label className="text-sm text-gray-500">Phone</label>
            <div className="font-medium">{profile.phone}</div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

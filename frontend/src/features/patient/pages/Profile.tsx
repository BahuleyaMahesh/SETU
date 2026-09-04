import React, { useState } from 'react';
import { Card, CardHeader, CardContent } from '../../../shared/components/Card';
import { Button } from '../../../shared/components/Button';
import { Input } from '../../../shared/components/Input';
import { Badge } from '../../../shared/components/Badge';

export const PatientProfile: React.FC = () => {
  const [profile, setProfile] = useState({
    mrn: 'MRN001',
    name: 'Ramesh Kumar',
    age: 66,
    gender: 'Male',
    phone: '+91-98765-43211',
    address: '456 Patient Lane, Bangalore',
    village: 'Village A',
    riskLevel: 'normal',
  });

  const [editing, setEditing] = useState(false);

  return (
    <div className="p-4 space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-semibold">My Profile</h1>
        <Button onClick={() => setEditing(!editing)}>
          {editing ? 'Cancel' : 'Edit'}
        </Button>
      </div>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-medium">Personal Information</h2>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-gray-500">MRN</label>
              <div className="font-medium">{profile.mrn}</div>
            </div>
            <div>
              <label className="text-sm text-gray-500">Name</label>
              <div className="font-medium">{profile.name}</div>
            </div>
            <div>
              <label className="text-sm text-gray-500">Age</label>
              <div className="font-medium">{profile.age}</div>
            </div>
            <div>
              <label className="text-sm text-gray-500">Gender</label>
              <div className="font-medium">{profile.gender}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-medium">Contact Information</h2>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input
            label="Phone"
            value={profile.phone}
            readOnly={!editing}
          />
          <Input
            label="Address"
            value={profile.address}
            readOnly={!editing}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-medium">Health Status</h2>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">Current Risk Level:</span>
            <Badge variant={profile.riskLevel === 'critical' ? 'danger' : profile.riskLevel === 'warning' ? 'warning' : 'success'}>
              {profile.riskLevel}
            </Badge>
          </div>
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

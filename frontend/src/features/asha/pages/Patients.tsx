import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from '../../../shared/components/Card';
import { Badge } from '../../../shared/components/Badge';
import { Button } from '../../../shared/components/Button';
import { Input } from '../../../shared/components/Input';
import { Link } from 'react-router-dom';

export const AshaPatients: React.FC = () => {
  const [patients, setPatients] = useState([
    { id: '1', mrn: 'MRN001', name: 'Ramesh Kumar', village: 'Village A', riskLevel: 'normal', lastCheckin: '2 days ago' },
    { id: '2', mrn: 'MRN002', name: 'Sita Devi', village: 'Village A', riskLevel: 'warning', lastCheckin: '1 week ago' },
    { id: '3', mrn: 'MRN003', name: 'Mohan Singh', village: 'Village B', riskLevel: 'critical', lastCheckin: '3 days ago' },
  ]);

  const [search, setSearch] = useState('');

  const filteredPatients = patients.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    p.mrn.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="p-4 space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-semibold">My Patients</h1>
        <Input
          placeholder="Search patients..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-64"
        />
      </div>

      <div className="grid gap-4">
        {filteredPatients.map((patient) => (
          <Card key={patient.id}>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-medium">{patient.name}</h3>
                  <p className="text-sm text-gray-500">MRN: {patient.mrn} | {patient.village}</p>
                </div>
                <Badge variant={patient.riskLevel === 'critical' ? 'danger' : patient.riskLevel === 'warning' ? 'warning' : 'success'}>
                  {patient.riskLevel}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Last check-in: {patient.lastCheckin}</span>
                <Link to={`/asha/patients/${patient.id}`}>
                  <Button size="sm" variant="outline">
                    View Details
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export const AshaPatientDetail: React.FC = () => {
  const [patient, setPatient] = useState({
    mrn: 'MRN001',
    name: 'Ramesh Kumar',
    age: 66,
    gender: 'Male',
    phone: '+91-98765-43211',
    address: '456 Patient Lane, Bangalore',
    village: 'Village A',
    riskLevel: 'normal',
  });

  const [checkins, setCheckins] = useState([
    { date: '2024-01-10', symptoms: ['fever', 'headache'], severity: 5 },
    { date: '2024-01-03', symptoms: ['cough'], severity: 2 },
  ]);

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center gap-4 mb-4">
        <Button variant="ghost" size="sm">Back</Button>
        <h1 className="text-xl font-semibold">Patient: {patient.name}</h1>
      </div>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-medium">Patient Information</h2>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-gray-500">MRN</label>
              <div className="font-medium">{patient.mrn}</div>
            </div>
            <div>
              <label className="text-sm text-gray-500">Age</label>
              <div className="font-medium">{patient.age}</div>
            </div>
            <div>
              <label className="text-sm text-gray-500">Gender</label>
              <div className="font-medium">{patient.gender}</div>
            </div>
            <div>
              <label className="text-sm text-gray-500">Phone</label>
              <div className="font-medium">{patient.phone}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-medium">Recent Check-ins</h2>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {checkins.map((checkin, index) => (
              <div key={index} className="bg-gray-50 p-3 rounded-lg">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-500">{checkin.date}</span>
                  <Badge variant={checkin.severity > 5 ? 'danger' : 'warning'}>
                    Severity: {checkin.severity}/10
                  </Badge>
                </div>
                <div className="mt-2">
                  {checkin.symptoms.map((symptom, i) => (
                    <Badge key={i} variant="primary" className="mr-2">
                      {symptom}
                    </Badge>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Button variant="primary" className="w-full" onClick={() => {}}>
        Create New Check-in
      </Button>
    </div>
  );
};

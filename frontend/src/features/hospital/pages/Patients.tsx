import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from '../../../shared/components/Card';
import { Badge } from '../../../shared/components/Badge';
import { Button } from '../../../shared/components/Button';
import { Input } from '../../../shared/components/Input';
import { Link } from 'react-router-dom';

export const HospitalPatients: React.FC = () => {
  const [patients, setPatients] = useState([
    { id: '1', mrn: 'MRN001', name: 'Ramesh Kumar', age: 66, village: 'Village A', riskLevel: 'normal' },
    { id: '2', mrn: 'MRN002', name: 'Sita Devi', age: 52, village: 'Village A', riskLevel: 'warning' },
    { id: '3', mrn: 'MRN003', name: 'Mohan Singh', age: 71, village: 'Village B', riskLevel: 'critical' },
  ]);

  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState<string>('all');

  const filteredPatients = patients.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(search.toLowerCase()) || p.mrn.includes(search);
    const matchesRisk = riskFilter === 'all' || p.riskLevel === riskFilter;
    return matchesSearch && matchesRisk;
  });

  return (
    <div className="p-4 space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-semibold">Patients</h1>
        <div className="flex gap-2">
          <Input
            placeholder="Search patients..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-64"
          />
          <select
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="px-3 py-2 border rounded-lg"
          >
            <option value="all">All Risks</option>
            <option value="normal">Normal</option>
            <option value="warning">Warning</option>
            <option value="critical">Critical</option>
          </select>
        </div>
      </div>

      <div className="grid gap-4">
        {filteredPatients.map((patient) => (
          <Card key={patient.id}>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-medium">{patient.name}</h3>
                  <p className="text-sm text-gray-500">
                    {patient.age} years | {patient.mrn} | {patient.village}
                  </p>
                </div>
                <Badge variant={patient.riskLevel === 'critical' ? 'danger' : patient.riskLevel === 'warning' ? 'warning' : 'success'}>
                  {patient.riskLevel}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">
                  Last visit: 2 days ago
                </span>
                <Link to={`/hospital/patients/${patient.id}`}>
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

export const HospitalPatientDetail: React.FC = () => {
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

  const [medicalHistory, setMedicalHistory] = useState([
    { date: '2024-01-10', condition: 'Hypertension', notes: 'Blood pressure elevated' },
    { date: '2024-01-03', condition: 'Diabetes', notes: 'Fasting glucose 140 mg/dL' },
  ]);

  const [recentCheckins, setRecentCheckins] = useState([
    { date: '2024-01-10', symptoms: ['fever', 'headache'], severity: 5, outcome: 'Normal' },
    { date: '2024-01-03', symptoms: ['cough'], severity: 2, outcome: 'Normal' },
  ]);

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center gap-4 mb-4">
        <Button variant="ghost" size="sm">Back</Button>
        <h1 className="text-xl font-semibold">Patient: {patient.name}</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader>
              <h2 className="text-lg font-medium">Medical History</h2>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {medicalHistory.map((item, index) => (
                  <div key={index} className="border-l-4 border-primary-500 pl-4 py-2">
                    <div className="flex justify-between">
                      <span className="font-medium">{item.condition}</span>
                      <span className="text-sm text-gray-500">{item.date}</span>
                    </div>
                    <div className="text-sm text-gray-600">{item.notes}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <h2 className="text-lg font-medium">Recent Check-ins</h2>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentCheckins.map((checkin, index) => (
                  <div key={index} className="bg-gray-50 p-3 rounded-lg">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">{checkin.date}</span>
                      <Badge variant={checkin.outcome === 'Normal' ? 'success' : 'danger'}>
                        {checkin.outcome}
                      </Badge>
                    </div>
                    <div className="mt-2">
                      {checkin.symptoms.map((symptom, i) => (
                        <Badge key={i} variant="primary" className="mr-2">
                          {symptom}
                        </Badge>
                      ))}
                    </div>
                    <div className="mt-2 text-sm">Severity: {checkin.severity}/10</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <h2 className="text-lg font-medium">Patient Info</h2>
            </CardHeader>
            <CardContent className="space-y-3">
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
              <div>
                <label className="text-sm text-gray-500">Address</label>
                <div className="text-sm text-gray-700">{patient.address}</div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <h2 className="text-lg font-medium">Actions</h2>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button className="w-full" variant="outline">Create Check-in</Button>
              <Button className="w-full" variant="outline">Create Alert</Button>
              <Button className="w-full" variant="outline">Call Patient</Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

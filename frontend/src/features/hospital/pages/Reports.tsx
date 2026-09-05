import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from '../../../shared/components/Card';
import { Button } from '../../../shared/components/Button';
import { Input } from '../../../shared/components/Input';
import { Badge } from '../../../shared/components/Badge';

export const HospitalReports: React.FC = () => {
  const [reports, setReports] = useState([
    { id: '1', type: 'Patient Report', date: '2024-01-15', status: 'ready' },
    { id: '2', type: 'Risk Analysis', date: '2024-01-14', status: 'ready' },
  ]);

  const [loading, setLoading] = useState(false);

  const handleGenerateReport = async (type: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/reports/${type.toLowerCase().replace(' ', '_')}`, {
        method: 'GET',
      });
      const data = await response.json();
      setReports(prev => [
        { id: Date.now().toString(), type, date: new Date().toISOString().split('T')[0], status: 'ready' },
        ...prev,
      ]);
    } catch (error) {
      console.error('Error generating report:', error);
    }
    setLoading(false);
  };

  const handleDownloadReport = async (id: string) => {
    console.log('Downloading report:', id);
    // In production, download the report
  };

  return (
    <div className="p-4 space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-semibold">Reports</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => handleGenerateReport('Patient Report')}>
          <CardHeader>
            <h2 className="text-lg font-medium">Patient Report</h2>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-500 mb-4">Generate comprehensive patient health reports</p>
            <Button size="sm" disabled={loading}>Generate</Button>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => handleGenerateReport('Risk Analysis')}>
          <CardHeader>
            <h2 className="text-lg font-medium">Risk Analysis</h2>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-500 mb-4">Analyze risk patterns across patient population</p>
            <Button size="sm" disabled={loading}>Generate</Button>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => handleGenerateReport('Alert Summary')}>
          <CardHeader>
            <h2 className="text-lg font-medium">Alert Summary</h2>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-500 mb-4">Summary of all alerts with resolution status</p>
            <Button size="sm" disabled={loading}>Generate</Button>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => handleGenerateReport('Follow-up Report')}>
          <CardHeader>
            <h2 className="text-lg font-medium">Follow-up Report</h2>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-500 mb-4">Track patient follow-up schedules and completion</p>
            <Button size="sm" disabled={loading}>Generate</Button>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <h2 className="text-lg font-medium">Generated Reports</h2>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {reports.map((report) => (
              <div key={report.id} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <div>
                  <div className="font-medium">{report.type}</div>
                  <div className="text-sm text-gray-500">{report.date}</div>
                </div>
                <div className="flex gap-2">
                  <Badge variant={report.status === 'ready' ? 'success' : 'warning'}>
                    {report.status}
                  </Badge>
                  <Button size="sm" onClick={() => handleDownloadReport(report.id)}>
                    Download
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

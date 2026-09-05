import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from '../../../shared/components/Card';
import { Badge } from '../../../shared/components/Badge';
import { Button } from '../../../shared/components/Button';

export const HospitalAlertQueue: React.FC = () => {
  const [alerts, setAlerts] = useState([
    {
      id: '1',
      patientName: 'Mohan Singh',
      severity: 'high',
      status: 'new',
      title: 'Critical condition detected',
      description: 'Breathing difficulty and chest pain',
      createdAt: '2024-01-15 10:30',
      patientId: '1',
    },
    {
      id: '2',
      patientName: 'Sita Devi',
      severity: 'medium',
      status: 'new',
      title: 'Elevated risk score',
      description: 'Risk level increased to warning',
      createdAt: '2024-01-15 09:15',
      patientId: '2',
    },
  ]);

  const [loading, setLoading] = useState(false);

  const handleAcknowledge = async (id: string) => {
    setLoading(true);
    try {
      await fetch(`/api/v1/alerts/${id}/acknowledge`, { method: 'PATCH' });
      setAlerts(prev => prev.map(a => a.id === id ? { ...a, status: 'acknowledged' } : a));
    } catch (error) {
      console.error('Error acknowledging alert:', error);
    }
    setLoading(false);
  };

  const handleResolve = async (id: string) => {
    setLoading(true);
    try {
      await fetch(`/api/v1/alerts/${id}/resolve`, { method: 'PATCH' });
      setAlerts(prev => prev.map(a => a.id === id ? { ...a, status: 'resolved' } : a));
    } catch (error) {
      console.error('Error resolving alert:', error);
    }
    setLoading(false);
  };

  const handleEscalate = async (id: string) => {
    setLoading(true);
    try {
      await fetch(`/api/v1/escalations/${id}/escalate-further`, { method: 'PATCH' });
      setAlerts(prev => prev.map(a => a.id === id ? { ...a, status: 'escalated' } : a));
    } catch (error) {
      console.error('Error escalating alert:', error);
    }
    setLoading(false);
  };

  return (
    <div className="p-4 space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-semibold">Alert Queue</h1>
        <Badge variant="danger">{alerts.filter(a => a.status === 'new').length} New Alerts</Badge>
      </div>

      <div className="grid gap-4">
        {alerts.map((alert) => (
          <Card key={alert.id}>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-medium">{alert.title}</h3>
                  <p className="text-sm text-gray-500">{alert.patientName} - {alert.createdAt}</p>
                </div>
                <div className="flex gap-2">
                  <Badge variant={alert.severity === 'high' ? 'danger' : 'warning'}>
                    {alert.severity}
                  </Badge>
                  <Badge variant="primary">
                    {alert.status}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-700 mb-4">{alert.description}</p>

              <div className="flex gap-2">
                {alert.status === 'new' && (
                  <Button size="sm" onClick={() => handleAcknowledge(alert.id)} disabled={loading}>
                    Acknowledge
                  </Button>
                )}
                <Button size="sm" variant="outline" onClick={() => handleEscalate(alert.id)} disabled={loading}>
                  Escalate
                </Button>
                <Button size="sm" variant="success" onClick={() => handleResolve(alert.id)} disabled={loading}>
                  Resolve
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

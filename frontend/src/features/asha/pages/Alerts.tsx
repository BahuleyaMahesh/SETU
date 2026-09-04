import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from '../../../shared/components/Card';
import { Badge } from '../../../shared/components/Badge';
import { Button } from '../../../shared/components/Button';

export const AshaAlerts: React.FC = () => {
  const [alerts, setAlerts] = useState([
    {
      id: '1',
      patientName: 'Ramesh Kumar',
      severity: 'high',
      status: 'new',
      title: 'Critical symptoms detected',
      description: 'Breathing difficulty and chest pain reported',
      createdAt: '2024-01-15 10:30',
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
      await fetch(`/api/v1/escalations`, { method: 'POST' });
      setAlerts(prev => prev.map(a => a.id === id ? { ...a, status: 'escalated' } : a));
    } catch (error) {
      console.error('Error escalating alert:', error);
    }
    setLoading(false);
  };

  return (
    <div className="p-4 space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-semibold">Alerts</h1>
        <Badge variant="danger">{alerts.filter(a => a.status === 'new').length} New</Badge>
      </div>

      <div className="grid gap-4">
        {alerts.map((alert) => (
          <Card key={alert.id}>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-medium">{alert.title}</h3>
                  <p className="text-sm text-gray-500">{alert.patientName}</p>
                </div>
                <Badge variant={alert.severity === 'high' ? 'danger' : 'warning'}>
                  {alert.severity}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="mb-3">
                <p className="text-sm text-gray-700">{alert.description}</p>
                <span className="text-xs text-gray-500 mt-1 block">{alert.createdAt}</span>
              </div>

              <div className="flex gap-2">
                {alert.status === 'new' && (
                  <Button size="sm" onClick={() => handleAcknowledge(alert.id)} disabled={loading}>
                    Acknowledge
                  </Button>
                )}
                <Button size="sm" variant="outline" onClick={() => handleEscalate(alert.id)} disabled={loading}>
                  Escalate
                </Button>
                {alert.status !== 'resolved' && (
                  <Button size="sm" variant="success" onClick={() => handleResolve(alert.id)} disabled={loading}>
                    Resolve
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

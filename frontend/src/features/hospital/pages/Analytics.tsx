import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from '../../../shared/components/Card';
import { Badge } from '../../../shared/components/Badge';

export const HospitalAnalytics: React.FC = () => {
  const [analytics, setAnalytics] = useState({
    totalPatients: 150,
    criticalPatients: 12,
    warningPatients: 35,
    stablePatients: 103,
    openAlerts: 8,
    recentEvaluations: 245,
  });

  const [riskTrend, setRiskTrend] = useState([
    { day: 'Mon', normal: 10, warning: 3, critical: 1 },
    { day: 'Tue', normal: 11, warning: 4, critical: 0 },
    { day: 'Wed', normal: 9, warning: 5, critical: 2 },
    { day: 'Thu', normal: 12, warning: 2, critical: 1 },
    { day: 'Fri', normal: 10, warning: 3, critical: 0 },
    { day: 'Sat', normal: 8, warning: 4, critical: 1 },
    { day: 'Sun', normal: 9, warning: 3, critical: 2 },
  ]);

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchAnalytics = async () => {
      setLoading(true);
      try {
        const response = await fetch('/api/v1/analytics/risk');
        const data = await response.json();
        // Update analytics with real data
      } catch (error) {
        console.error('Error fetching analytics:', error);
      }
      setLoading(false);
    };
    fetchAnalytics();
  }, []);

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-semibold">Analytics Dashboard</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent>
            <div className="text-sm text-gray-500">Total Patients</div>
            <div className="text-2xl font-bold">{analytics.totalPatients}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div className="text-sm text-gray-500">Critical</div>
            <div className="text-2xl font-bold text-red-500">{analytics.criticalPatients}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div className="text-sm text-gray-500">Warning</div>
            <div className="text-2xl font-bold text-yellow-500">{analytics.warningPatients}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div className="text-sm text-gray-500">Open Alerts</div>
            <div className="text-2xl font-bold text-primary-500">{analytics.openAlerts}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="h-[400px]">
          <CardHeader>
            <h2 className="text-lg font-medium">Risk Distribution</h2>
          </CardHeader>
          <CardContent>
            <div className="flex items-end justify-between h-64 gap-2">
              {riskTrend.map((item, index) => (
                <div key={index} className="flex flex-col items-center gap-2 flex-1">
                  <div className="flex items-end gap-1 h-full">
                    <div style={{ height: `${(item.normal / 15) * 100}%`, width: '100%' }} className="bg-green-500 rounded-t"></div>
                    <div style={{ height: `${(item.warning / 15) * 100}%`, width: '100%' }} className="bg-yellow-500 rounded-t"></div>
                    <div style={{ height: `${(item.critical / 15) * 100}%`, width: '100%' }} className="bg-red-500 rounded-t"></div>
                  </div>
                  <span className="text-xs">{item.day}</span>
                </div>
              ))}
            </div>
            <div className="flex justify-center gap-4 mt-4">
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-green-500"></div>
                <span className="text-xs">Normal</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-yellow-500"></div>
                <span className="text-xs">Warning</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 bg-red-500"></div>
                <span className="text-xs">Critical</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h2 className="text-lg font-medium">Key Metrics</h2>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Risk Evaluations (Last 24h)</span>
                <Badge variant="primary">{analytics.recentEvaluations}</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Critical Patient Visits</span>
                <Badge variant="danger">{analytics.criticalPatients}</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Alert Resolution Rate</span>
                <Badge variant="success">92%</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

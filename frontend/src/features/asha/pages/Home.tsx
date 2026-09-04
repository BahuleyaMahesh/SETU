import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../app/auth/AuthProvider';
import { Card } from '../../../shared/components/Card';
import { Button } from '../../../shared/components/Button';
import { Badge } from '../../../shared/components/Badge';
import { Users, AlertTriangle, MapPin, Phone, ShieldAlert, ArrowRight, Activity, CheckCircle2 } from 'lucide-react';

export const AshaHome: React.FC = () => {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [caseload, setCaseload] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [token, user?.asha_worker_id]);

  const fetchData = async () => {
    if (!user?.asha_worker_id) {
      setLoading(false);
      return;
    }
    try {
      const [caseloadRes, alertsRes] = await Promise.all([
        fetch(`/api/v1/asha/${user.asha_worker_id}/caseload`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`/api/v1/alerts?status=new`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      if (caseloadRes.ok) {
        const caseloadData = await caseloadRes.json();
        setCaseload(caseloadData);
      }
      if (alertsRes.ok) {
        const alertsData = await alertsRes.json();
        setAlerts(Array.isArray(alertsData) ? alertsData : []);
      }
    } catch (error) {
      console.error('Error fetching ASHA dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-16">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600" />
      </div>
    );
  }

  const criticalCount = caseload?.critical_patients ?? 0;
  const warningCount = caseload?.warning_patients ?? 0;
  const normalCount = caseload?.stable_patients ?? 0;
  const totalPatients = caseload?.total_patients ?? (criticalCount + warningCount + normalCount);

  return (
    <div className="space-y-6">
      {/* Field Worker Header */}
      <div className="bg-gradient-to-r from-teal-700 to-emerald-700 text-white rounded-2xl p-6 shadow-md">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              Field Overview: {user?.full_name || 'ASHA Worker'}
            </h1>
            <p className="text-teal-100 text-sm mt-1">
              Monitoring active post-discharge patients in assigned rural block.
            </p>
          </div>
          <Badge variant="success" className="bg-emerald-500/20 text-emerald-100 border border-emerald-400/30">
            Active Status
          </Badge>
        </div>
      </div>

      {/* Caseload Summary */}
      <Card className="p-6">
        <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2 mb-4">
          <Users className="w-5 h-5 text-teal-600" />
          <span>Patient Caseload Triage</span>
        </h2>
        <div className="grid grid-cols-3 gap-3">
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-center">
            <p className="text-2xl font-black text-slate-800">{totalPatients}</p>
            <p className="text-xs text-slate-500 font-medium uppercase mt-0.5">Total Assigned</p>
          </div>
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-center">
            <p className="text-2xl font-black text-emerald-700">{normalCount}</p>
            <p className="text-xs text-emerald-700 font-medium uppercase mt-0.5">Stable</p>
          </div>
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-center">
            <p className="text-2xl font-black text-red-600">{criticalCount}</p>
            <p className="text-xs text-red-600 font-medium uppercase mt-0.5">Critical</p>
          </div>
        </div>
      </Card>

      {/* Open Alerts Section */}
      <Card className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-600" />
            <span>Open Clinical Alerts</span>
          </h3>
          <span className="text-xs font-semibold bg-red-100 text-red-700 px-2.5 py-0.5 rounded-full">
            {alerts.length} Active
          </span>
        </div>

        {alerts.length === 0 ? (
          <div className="p-4 bg-emerald-50/60 dark:bg-emerald-950/40 border border-emerald-200/60 dark:border-emerald-800/40 rounded-xl text-center text-emerald-800 text-sm flex items-center justify-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>No urgent alerts pending acknowledgment in your block.</span>
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map(alert => (
              <div key={alert.id} className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-center justify-between">
                <div>
                  <p className="font-bold text-red-900 text-sm">{alert.title || alert.trigger_reason || 'High Risk Symptoms'}</p>
                  <p className="text-xs text-red-700 mt-0.5">{alert.description || 'Patient reported critical discomfort level.'}</p>
                </div>
                <Button
                  size="sm"
                  onClick={() => navigate('/asha/alerts')}
                  className="bg-red-600 hover:bg-red-500 text-white text-xs font-semibold rounded-lg px-3 py-1.5 flex items-center gap-1"
                >
                  <span>Triage</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Quick Action Navigation */}
      <Card className="p-6">
        <h3 className="text-lg font-bold text-slate-800 mb-4">Field Actions</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <Button
            onClick={() => navigate('/asha/map')}
            className="w-full bg-teal-700 hover:bg-teal-600 text-white font-semibold py-3 rounded-xl flex items-center justify-center gap-2"
          >
            <MapPin className="w-4 h-4" />
            <span>Field Patient Map</span>
          </Button>

          <Button
            onClick={() => navigate('/asha/patients')}
            variant="outline"
            className="w-full font-semibold py-3 rounded-xl flex items-center justify-center gap-2 border-slate-300 hover:bg-slate-50"
          >
            <Users className="w-4 h-4 text-slate-700" />
            <span>Patient Roster</span>
          </Button>

          <Button
            onClick={() => navigate('/asha/alerts')}
            variant="outline"
            className="w-full font-semibold py-3 rounded-xl flex items-center justify-center gap-2 border-slate-300 hover:bg-slate-50"
          >
            <ShieldAlert className="w-4 h-4 text-slate-700" />
            <span>Emergency Queue</span>
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default AshaHome;

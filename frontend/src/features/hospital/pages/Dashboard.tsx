import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../app/auth/AuthProvider';
import { Card, CardHeader, CardContent } from '../../../shared/components/Card';
import { Badge } from '../../../shared/components/Badge';
import { Button } from '../../../shared/components/Button';
import { Users, AlertTriangle, Activity, ShieldAlert, BarChart3, MapPin, FileText, ArrowUpRight } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export const HospitalDashboard: React.FC = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalPatients: 42,
    criticalPatients: 3,
    warningPatients: 9,
    stablePatients: 30,
    openAlerts: 4,
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardStats();
  }, [token]);

  const fetchDashboardStats = async () => {
    try {
      const res = await fetch('/api/v1/analytics/risk-distribution', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setStats(prev => ({
          ...prev,
          totalPatients: data.total || prev.totalPatients,
          criticalPatients: data.critical || prev.criticalPatients,
          warningPatients: data.warning || prev.warningPatients,
          stablePatients: data.normal || prev.stablePatients,
        }));
      }
    } catch (e) {
      console.error('Failed to load dashboard stats:', e);
    } finally {
      setLoading(false);
    }
  };

  const riskDistributionData = [
    { name: 'Stable', count: stats.stablePatients, fill: '#10b981' },
    { name: 'Warning', count: stats.warningPatients, fill: '#f59e0b' },
    { name: 'Critical', count: stats.criticalPatients, fill: '#ef4444' },
  ];

  if (loading) {
    return (
      <div className="flex justify-center items-center py-16">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 bg-gradient-to-r from-slate-900 via-slate-800 to-sky-950 text-white p-6 rounded-2xl shadow-md border border-slate-800">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight">Hospital Command Center</h1>
          <p className="text-slate-400 text-sm mt-1">Real-time triage dashboard for post-discharge rural patient cohorts.</p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            onClick={() => navigate('/hospital/alerts')}
            className="bg-red-600 hover:bg-red-500 text-white font-semibold text-xs px-4 py-2.5 rounded-xl flex items-center gap-2 shadow-lg shadow-red-600/20"
          >
            <ShieldAlert className="w-4 h-4" />
            <span>View {stats.openAlerts} Open Alerts</span>
          </Button>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-5 border-slate-200 shadow-sm">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Patients</p>
              <h3 className="text-3xl font-black text-slate-900 mt-1">{stats.totalPatients}</h3>
            </div>
            <div className="p-2.5 bg-sky-50 text-sky-600 rounded-xl">
              <Users className="w-5 h-5" />
            </div>
          </div>
          <p className="text-xs text-slate-500 mt-3 flex items-center gap-1">
            <span className="text-emerald-600 font-bold">100%</span> active monitoring
          </p>
        </Card>

        <Card className="p-5 border-red-200/80 bg-red-50/30 shadow-sm">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-semibold text-red-600 uppercase tracking-wider">Critical Escalations</p>
              <h3 className="text-3xl font-black text-red-600 mt-1">{stats.criticalPatients}</h3>
            </div>
            <div className="p-2.5 bg-red-100 text-red-600 rounded-xl">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>
          <p className="text-xs text-red-700 mt-3 font-medium">Requires clinical review</p>
        </Card>

        <Card className="p-5 border-amber-200/80 bg-amber-50/30 shadow-sm">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-semibold text-amber-700 uppercase tracking-wider">Warning Tier</p>
              <h3 className="text-3xl font-black text-amber-600 mt-1">{stats.warningPatients}</h3>
            </div>
            <div className="p-2.5 bg-amber-100 text-amber-600 rounded-xl">
              <Activity className="w-5 h-5" />
            </div>
          </div>
          <p className="text-xs text-amber-700 mt-3 font-medium">ASHA check-in requested</p>
        </Card>

        <Card className="p-5 border-emerald-200/80 bg-emerald-50/30 shadow-sm">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wider">Stable Cohort</p>
              <h3 className="text-3xl font-black text-emerald-600 mt-1">{stats.stablePatients}</h3>
            </div>
            <div className="p-2.5 bg-emerald-100 text-emerald-600 rounded-xl">
              <Users className="w-5 h-5" />
            </div>
          </div>
          <p className="text-xs text-emerald-700 mt-3 font-medium">Daily voice check-ins normal</p>
        </Card>
      </div>

      {/* Analytics & Quick Actions Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <Card className="lg:col-span-8 p-6 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-lg font-bold text-slate-900">Cohort Risk Level Breakdown</h2>
              <p className="text-xs text-slate-500 mt-0.5">Automated deterministic risk tier categorization</p>
            </div>
            <BarChart3 className="w-5 h-5 text-slate-400" />
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskDistributionData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} />
                <Tooltip cursor={{ fill: '#f1f5f9' }} />
                <Bar dataKey="count" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="lg:col-span-4 p-6 shadow-sm">
          <h2 className="text-lg font-bold text-slate-900 mb-4">Quick Navigation</h2>
          <div className="space-y-2.5">
            <Button
              onClick={() => navigate('/hospital/patients')}
              className="w-full bg-slate-800 hover:bg-slate-700 text-white font-semibold py-3 rounded-xl flex items-center justify-between text-sm"
            >
              <div className="flex items-center gap-2.5">
                <Users className="w-4 h-4 text-sky-400" />
                <span>Patient Directory</span>
              </div>
              <ArrowUpRight className="w-4 h-4 text-slate-400" />
            </Button>

            <Button
              onClick={() => navigate('/hospital/alerts')}
              variant="outline"
              className="w-full font-semibold py-3 rounded-xl flex items-center justify-between text-sm border-slate-200 hover:bg-slate-50"
            >
              <div className="flex items-center gap-2.5">
                <AlertTriangle className="w-4 h-4 text-red-500" />
                <span>Emergency Alert Queue</span>
              </div>
              <ArrowUpRight className="w-4 h-4 text-slate-400" />
            </Button>

            <Button
              onClick={() => navigate('/hospital/reports')}
              variant="outline"
              className="w-full font-semibold py-3 rounded-xl flex items-center justify-between text-sm border-slate-200 hover:bg-slate-50"
            >
              <div className="flex items-center gap-2.5">
                <FileText className="w-4 h-4 text-emerald-500" />
                <span>Clinical Reports</span>
              </div>
              <ArrowUpRight className="w-4 h-4 text-slate-400" />
            </Button>

            <Button
              onClick={() => navigate('/hospital/map')}
              variant="outline"
              className="w-full font-semibold py-3 rounded-xl flex items-center justify-between text-sm border-slate-200 hover:bg-slate-50"
            >
              <div className="flex items-center gap-2.5">
                <MapPin className="w-4 h-4 text-teal-500" />
                <span>Regional Patient Map</span>
              </div>
              <ArrowUpRight className="w-4 h-4 text-slate-400" />
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default HospitalDashboard;

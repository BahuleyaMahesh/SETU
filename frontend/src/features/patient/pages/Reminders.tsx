import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../app/auth/AuthProvider';
import { Card, CardHeader, CardContent } from '../../../shared/components/Card';
import { Button } from '../../../shared/components/Button';
import { Badge } from '../../../shared/components/Badge';
import { Bell, Pill, Calendar, CheckCircle2, Clock } from 'lucide-react';
import { ScheduleCallPanel } from '../../../shared/components/ScheduleCallPanel';

export const PatientReminders: React.FC = () => {
  const { user, token } = useAuth();
  const [reminders, setReminders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReminders();
  }, [token]);

  const fetchReminders = async () => {
    try {
      const response = await fetch('/api/v1/reminders/', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setReminders(data);
      }
    } catch (error) {
      console.error('Error fetching reminders:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/reminders/${id}/complete`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setReminders(prev => prev.map(r => r.id === id ? { ...r, status: 'completed' } : r));
      }
    } catch (error) {
      console.error('Error completing reminder:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-16">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Bell className="w-5 h-5 text-sky-600" />
            <span>Care & Medication Reminders</span>
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">Stay on track with post-discharge medications & checkups.</p>
        </div>
      </div>

      {user?.patient_id && (
        <Card className="p-5 border-slate-200 rounded-2xl">
          <ScheduleCallPanel patientId={user.patient_id} />
        </Card>
      )}

      {reminders.length === 0 ? (
        <Card className="p-8 text-center bg-slate-50 border border-slate-200 rounded-2xl">
          <Clock className="w-10 h-10 text-slate-400 mx-auto mb-3" />
          <h3 className="font-bold text-slate-700 text-base">No Pending Reminders</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            You are all caught up! Scheduled medication and follow-up alerts will appear here.
          </p>
        </Card>
      ) : (
        <div className="grid gap-3">
          {reminders.map(reminder => {
            const isMed = reminder.type === 'medication';
            const isCompleted = reminder.status === 'completed';
            return (
              <Card key={reminder.id} className="p-5 border-slate-200 hover:border-slate-300 transition-all shadow-sm">
                <div className="flex justify-between items-start">
                  <div className="flex items-start gap-3">
                    <div className={`p-2.5 rounded-xl ${isMed ? 'bg-sky-50 text-sky-600' : 'bg-teal-50 text-teal-600'}`}>
                      {isMed ? <Pill className="w-5 h-5" /> : <Calendar className="w-5 h-5" />}
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-900 text-sm capitalize">{reminder.title || reminder.type}</h3>
                      <p className="text-xs text-slate-500 mt-1">{reminder.description || 'Scheduled care event'}</p>
                    </div>
                  </div>
                  <Badge variant={isCompleted ? 'success' : 'warning'}>
                    {reminder.status || 'pending'}
                  </Badge>
                </div>

                {!isCompleted && (
                  <div className="mt-4 pt-3 border-t border-slate-100 flex justify-end">
                    <Button
                      size="sm"
                      onClick={() => handleComplete(reminder.id)}
                      className="bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs rounded-lg px-3 py-1.5 flex items-center gap-1.5"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Mark Complete</span>
                    </Button>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

export const AshaReminders: React.FC = () => {
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-slate-900">Field Patient Reminders</h1>
      <Card className="p-8 text-center text-slate-500">
        All automated reminders sent to patients in your assigned block are tracked in real-time.
      </Card>
    </div>
  );
};

export default PatientReminders;

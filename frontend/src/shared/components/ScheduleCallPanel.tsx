import React, { useEffect, useState } from 'react';
import { useAuth } from '../../app/auth/AuthProvider';
import { Card } from './Card';
import { Phone, CalendarClock, X } from 'lucide-react';

interface ScheduleCallPanelProps {
  /** The patient to schedule the call for — patient, ASHA, or hospital
   * staff can all use this for a patient they're authorized to see. */
  patientId: string;
}

export const ScheduleCallPanel: React.FC<ScheduleCallPanelProps> = ({ patientId }) => {
  const { token } = useAuth();
  const [scheduledCalls, setScheduledCalls] = useState<any[]>([]);
  const [time, setTime] = useState('');
  const [repeatDaily, setRepeatDaily] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchScheduledCalls();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, patientId]);

  const fetchScheduledCalls = async () => {
    if (!patientId) return;
    try {
      const res = await fetch(`/api/v1/reminders/patient/${patientId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setScheduledCalls(data.filter((r: any) => r.reminder_type === 'checkin_call'));
      }
    } catch (error) {
      console.error('Error fetching scheduled calls:', error);
    }
  };

  const handleSchedule = async () => {
    if (!time) {
      setMessage('Pick a time first.');
      return;
    }
    // Just a clock time is enough — the call repeats at that time, so the
    // date it starts on doesn't matter to the patient. Take the next
    // upcoming occurrence of that time (today if it hasn't passed yet,
    // otherwise tomorrow) in the browser's own local timezone, then convert
    // to a real UTC instant for the backend the same way the old
    // datetime-local picker did.
    const [hours, minutes] = time.split(':').map(Number);
    const next = new Date();
    next.setHours(hours, minutes, 0, 0);
    if (next.getTime() <= Date.now()) {
      next.setDate(next.getDate() + 1);
    }
    const utcIso = next.toISOString();

    setSubmitting(true);
    setMessage('');
    try {
      const res = await fetch('/api/v1/calls/schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ patient_id: patientId, scheduled_at: utcIso, repeat_daily: repeatDaily }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Could not schedule the call');
      }
      setTime('');
      setRepeatDaily(false);
      setMessage('Call scheduled.');
      await fetchScheduledCalls();
    } catch (error: any) {
      setMessage(error.message || 'Could not schedule the call');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = async (reminderId: string) => {
    try {
      const res = await fetch(`/api/v1/reminders/${reminderId}/cancel`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setScheduledCalls((prev) => prev.filter((r) => r.id !== reminderId));
      }
    } catch (error) {
      console.error('Error cancelling scheduled call:', error);
    }
  };

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
        <Phone className="w-4 h-4 text-emerald-600" />
        Schedule a Check-in Call
      </h3>

      <div className="flex flex-col sm:flex-row gap-2 items-start sm:items-center">
        <input
          type="time"
          value={time}
          onChange={(e) => setTime(e.target.value)}
          className="text-sm border border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 rounded-lg px-3 py-2"
        />
        <label className="flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-400">
          <input type="checkbox" checked={repeatDaily} onChange={(e) => setRepeatDaily(e.target.checked)} />
          Repeat daily
        </label>
        <button
          onClick={handleSchedule}
          disabled={submitting}
          className="inline-flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs px-3 py-2 rounded-lg disabled:opacity-60"
        >
          <CalendarClock className="w-3.5 h-3.5" />
          {submitting ? 'Scheduling...' : 'Schedule Call'}
        </button>
      </div>

      {message && <p className="text-xs text-slate-500 dark:text-slate-400">{message}</p>}

      {scheduledCalls.length > 0 && (
        <div className="grid gap-1.5">
          {scheduledCalls.map((r) => (
            <Card key={r.id} className="p-3 flex items-center justify-between border-slate-200 dark:border-slate-700">
              <div className="text-xs text-slate-700 dark:text-slate-300">
                <span className="font-semibold">
                  {/* Backend sends a naive-UTC timestamp with no timezone
                     suffix (e.g. "2026-09-05T13:00:00") — the JS Date
                     constructor treats that as LOCAL time, not UTC, so
                     without appending "Z" this would silently render off
                     by the browser's UTC offset (confirmed live: a 6:30 PM
                     IST call showed as "1:00 PM"). */}
                  {new Date(r.scheduled_at.endsWith('Z') ? r.scheduled_at : `${r.scheduled_at}Z`).toLocaleString(undefined, {
                    weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
                  })}
                </span>
                {r.schedule_type === 'daily' && <span className="ml-2 text-emerald-600">(repeats daily)</span>}
                <span className="ml-2 text-slate-400">— {r.status}</span>
              </div>
              {r.status === 'scheduled' && (
                <button onClick={() => handleCancel(r.id)} className="text-slate-400 hover:text-red-500" title="Cancel">
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default ScheduleCallPanel;

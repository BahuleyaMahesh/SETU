import React, { useEffect, useState } from 'react';
import { useAuth } from '../../app/auth/AuthProvider';
import { Bell, Clock, Send, X, Plus, Check } from 'lucide-react';

/** Backend timestamps are naive UTC with no timezone suffix, so a plain
 * `new Date(str)` would read them as local time and land hours off (IST is
 * +5:30). Append the Z before parsing. */
const parseUtc = (value: string) => new Date(value.endsWith('Z') ? value : `${value}Z`);

/** Local "HH:MM" for an <input type="time">, from a stored UTC timestamp. */
const toLocalHHMM = (value: string) => {
  const d = parseUtc(value);
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
};

interface MedicationRemindersPanelProps {
  patientId: string;
  /** Bump this when a prescription upload finishes so newly auto-created
   * reminders appear without a page reload. */
  refreshKey?: number;
}

/** Schedule, retime, send and cancel a patient's medication reminders.
 *
 * The prescription's frequency text ("1-0-1", "twice daily", "morning and
 * night") auto-creates these at default times when a prescription is
 * uploaded — but a real patient's routine differs from the defaults, so
 * every reminder is editable here. Times are shown and entered as LOCAL
 * (IST) clock times; the backend converts to the naive-UTC the DB stores.
 *
 * Shared by the patient's own Meds page and the ASHA/hospital patient
 * detail panel, so a fix here applies to all three roles. */
export const MedicationRemindersPanel: React.FC<MedicationRemindersPanelProps> = ({
  patientId,
  refreshKey = 0,
}) => {
  const { token } = useAuth();
  const [reminders, setReminders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTime, setEditTime] = useState('');
  const [busyId, setBusyId] = useState<string | null>(null);
  const [showAdd, setShowAdd] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newTime, setNewTime] = useState('08:00');
  const [actionMsg, setActionMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const authHeaders = { Authorization: `Bearer ${token}` };

  const fetchReminders = async () => {
    if (!patientId) {
      setLoading(false);
      return;
    }
    try {
      const res = await fetch(`/api/v1/reminders/patient/${patientId}`, { headers: authHeaders });
      if (res.ok) {
        const all = await res.json();
        // Scheduled check-in CALLS live in the same Reminder table but are
        // managed by ScheduleCallPanel — showing them here too would be a
        // confusing duplicate with a meaningless "Send now" (it would place
        // a phone call, not send a medication message).
        setReminders(all.filter((r: any) => r.reminder_type !== 'checkin_call'));
      }
    } catch (error) {
      console.error('Error fetching reminders:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReminders();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, patientId, refreshKey]);

  const handleReschedule = async (reminderId: string) => {
    if (!editTime) return;
    setBusyId(reminderId);
    setActionMsg(null);
    try {
      const res = await fetch(`/api/v1/reminders/${reminderId}/reschedule`, {
        method: 'PATCH',
        headers: { ...authHeaders, 'Content-Type': 'application/json' },
        body: JSON.stringify({ time: editTime }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Could not reschedule');
      }
      setEditingId(null);
      setActionMsg({ ok: true, text: 'Reminder time updated.' });
      await fetchReminders();
    } catch (error: any) {
      setActionMsg({ ok: false, text: error.message || 'Could not reschedule' });
    } finally {
      setBusyId(null);
    }
  };

  const handleSendNow = async (reminderId: string) => {
    setBusyId(reminderId);
    setActionMsg(null);
    try {
      const res = await fetch(`/api/v1/reminders/${reminderId}/send`, {
        method: 'POST',
        headers: authHeaders,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || 'Could not send');
      setActionMsg({ ok: true, text: 'Reminder sent now.' });
      await fetchReminders();
    } catch (error: any) {
      setActionMsg({ ok: false, text: error.message || 'Could not send this reminder' });
    } finally {
      setBusyId(null);
    }
  };

  const handleCancel = async (reminderId: string) => {
    setBusyId(reminderId);
    setActionMsg(null);
    try {
      const res = await fetch(`/api/v1/reminders/${reminderId}/cancel`, {
        method: 'PATCH',
        headers: authHeaders,
      });
      if (!res.ok) throw new Error('Could not cancel');
      setActionMsg({ ok: true, text: 'Reminder cancelled.' });
      await fetchReminders();
    } catch (error: any) {
      setActionMsg({ ok: false, text: error.message || 'Could not cancel' });
    } finally {
      setBusyId(null);
    }
  };

  const handleAddReminder = async () => {
    if (!newTitle.trim() || !newTime) return;
    setBusyId('new');
    setActionMsg(null);
    try {
      const res = await fetch('/api/v1/reminders/medication', {
        method: 'POST',
        headers: { ...authHeaders, 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_id: patientId, title: newTitle.trim(), time: newTime }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Could not create reminder');
      }
      setNewTitle('');
      setNewTime('08:00');
      setShowAdd(false);
      setActionMsg({ ok: true, text: 'Reminder added.' });
      await fetchReminders();
    } catch (error: any) {
      setActionMsg({ ok: false, text: error.message || 'Could not create reminder' });
    } finally {
      setBusyId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-6">
        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-sky-600" />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between gap-2 mb-2">
        <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
          <Bell className="w-3.5 h-3.5 text-blue-600" />
          Medication Reminders ({reminders.filter((r: any) => r.status === 'scheduled').length} active)
        </h4>
        <button
          onClick={() => { setShowAdd((s) => !s); setActionMsg(null); }}
          className="inline-flex items-center gap-1 text-xs font-semibold text-sky-600 hover:text-sky-500"
        >
          <Plus className="w-3.5 h-3.5" />
          Add reminder
        </button>
      </div>

      {showAdd && (
        <div className="mb-2 p-3 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-xl flex flex-col sm:flex-row gap-2 sm:items-center">
          <input
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="e.g. Take Metformin"
            className="flex-1 text-xs px-2.5 py-2 border border-slate-300 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 rounded-lg"
          />
          <input
            type="time"
            value={newTime}
            onChange={(e) => setNewTime(e.target.value)}
            className="text-xs px-2.5 py-2 border border-slate-300 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 rounded-lg"
          />
          <button
            onClick={handleAddReminder}
            disabled={busyId === 'new' || !newTitle.trim()}
            className="inline-flex items-center justify-center gap-1 bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs px-3 py-2 rounded-lg disabled:opacity-60"
          >
            <Check className="w-3.5 h-3.5" />
            {busyId === 'new' ? 'Adding...' : 'Add'}
          </button>
        </div>
      )}

      {actionMsg && (
        <p className={`text-xs font-medium mb-2 ${actionMsg.ok ? 'text-emerald-600' : 'text-red-600'}`}>
          {actionMsg.text}
        </p>
      )}

      {reminders.length === 0 ? (
        <p className="text-xs text-slate-500 italic">
          No reminders yet — upload a prescription to schedule them automatically, or add one manually.
        </p>
      ) : (
        <div className="grid gap-1.5">
          {reminders.map((r: any) => {
            const isEditing = editingId === r.id;
            const busy = busyId === r.id;
            const cancelled = r.status === 'cancelled';
            return (
              <div
                key={r.id}
                className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2"
              >
                <div className="flex-1 min-w-0">
                  <span className={`font-medium ${cancelled ? 'text-slate-400 line-through' : 'text-slate-700 dark:text-slate-300'}`}>
                    {r.title}
                  </span>
                  <span className="ml-2 text-slate-400">
                    {parseUtc(r.scheduled_at).toLocaleString(undefined, {
                      weekday: 'short', hour: 'numeric', minute: '2-digit',
                    })}
                    {r.schedule_type === 'daily' ? ' · daily' : ''}
                    {r.status !== 'scheduled' ? ` · ${r.status}` : ''}
                  </span>
                </div>

                {isEditing ? (
                  <div className="flex items-center gap-1.5">
                    <input
                      type="time"
                      value={editTime}
                      onChange={(e) => setEditTime(e.target.value)}
                      className="text-xs px-2 py-1.5 border border-slate-300 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 rounded-lg"
                    />
                    <button
                      onClick={() => handleReschedule(r.id)}
                      disabled={busy}
                      className="inline-flex items-center gap-1 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-2.5 py-1.5 rounded-lg disabled:opacity-60"
                    >
                      <Check className="w-3.5 h-3.5" />
                      {busy ? 'Saving' : 'Save'}
                    </button>
                    <button onClick={() => setEditingId(null)} className="text-slate-400 hover:text-slate-600">
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    <button
                      onClick={() => { setEditingId(r.id); setEditTime(toLocalHHMM(r.scheduled_at)); setActionMsg(null); }}
                      title="Change time"
                      className="inline-flex items-center gap-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-semibold px-2.5 py-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
                    >
                      <Clock className="w-3.5 h-3.5" />
                      Time
                    </button>
                    <button
                      onClick={() => handleSendNow(r.id)}
                      disabled={busy}
                      title="Send this reminder immediately"
                      className="inline-flex items-center gap-1 bg-sky-600 hover:bg-sky-500 text-white font-semibold px-2.5 py-1.5 rounded-lg disabled:opacity-60"
                    >
                      <Send className="w-3.5 h-3.5" />
                      {busy ? 'Sending' : 'Send now'}
                    </button>
                    {!cancelled && (
                      <button
                        onClick={() => handleCancel(r.id)}
                        disabled={busy}
                        title="Cancel reminder"
                        className="text-slate-400 hover:text-red-500 disabled:opacity-60"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default MedicationRemindersPanel;

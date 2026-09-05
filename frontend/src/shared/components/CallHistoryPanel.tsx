import React from 'react';
import { PhoneCall, PhoneOff, AlertTriangle, Mic } from 'lucide-react';

interface CallRecord {
  id: string;
  status: string;
  call_type?: string;
  call_direction?: string;
  duration?: number;
  created_at: string;
  dtmf_input?: string | null;
  speech_transcript?: string | null;
  recording_url?: string | null;
  to_number?: string | null;
}

interface CallHistoryPanelProps {
  calls?: CallRecord[];
}

/** What the patient actually said on their automated check-in calls.
 * The backend has stored transcripts/keypresses/recordings on every Call
 * row for a while, and returns them on GET /api/v1/patients/{id} as
 * `calls` — but nothing rendered them, so the whole point of the AI phone
 * check-in (bringing the patient's own words back to their care team)
 * never reached the people who needed it. */

const DTMF_MEANING: Record<string, string> = {
  '1': 'Pressed 1 — feeling fine',
  '2': 'Pressed 2 — wanted to report symptoms',
  '3': 'Pressed 3 — EMERGENCY',
};

const statusStyle = (status: string) => {
  if (status === 'completed') return 'bg-emerald-100 text-emerald-700 border-emerald-200';
  if (status === 'failed') return 'bg-red-100 text-red-700 border-red-200';
  if (status === 'needs_review') return 'bg-amber-100 text-amber-700 border-amber-200';
  return 'bg-slate-100 text-slate-600 border-slate-200';
};

export const CallHistoryPanel: React.FC<CallHistoryPanelProps> = ({ calls }) => {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
        <PhoneCall className="w-4 h-4 text-sky-600" />
        Check-in Call History
      </h3>

      {!calls || calls.length === 0 ? (
        <p className="text-xs text-slate-500 italic">No check-in calls placed yet.</p>
      ) : (
        <div className="space-y-2">
          {calls.slice(0, 8).map((call) => {
            const needsReview = call.status === 'needs_review';
            const failed = call.status === 'failed';
            return (
              <div
                key={call.id}
                className="p-3 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-xl space-y-1.5"
              >
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <span className="text-xs text-slate-500 dark:text-slate-400">
                    {/* Backend sends naive UTC with no timezone suffix — append
                       Z so the browser doesn't read it as local time. */}
                    {new Date(
                      call.created_at.endsWith('Z') ? call.created_at : `${call.created_at}Z`
                    ).toLocaleString(undefined, {
                      month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
                    })}
                    {call.duration ? ` · ${call.duration}s` : ''}
                  </span>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border ${statusStyle(call.status)}`}>
                    {call.status.replace('_', ' ')}
                  </span>
                </div>

                {call.dtmf_input && DTMF_MEANING[call.dtmf_input] && (
                  <div className={`text-xs font-semibold ${call.dtmf_input === '3' ? 'text-red-600' : 'text-slate-700 dark:text-slate-300'}`}>
                    {DTMF_MEANING[call.dtmf_input]}
                  </div>
                )}

                {call.speech_transcript ? (
                  <div className="flex items-start gap-1.5 text-xs text-slate-700 dark:text-slate-300">
                    <Mic className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-sky-600" />
                    <span className="italic">"{call.speech_transcript}"</span>
                  </div>
                ) : needsReview ? (
                  <div className="flex items-start gap-1.5 text-xs text-amber-700 dark:text-amber-400 font-medium">
                    <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                    <span>Patient responded but speech could not be transcribed — listen to the recording or call back.</span>
                  </div>
                ) : failed ? (
                  <div className="flex items-start gap-1.5 text-xs text-red-600">
                    <PhoneOff className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                    <span>Call could not be placed.</span>
                  </div>
                ) : null}

                {call.recording_url && (
                  <audio controls preload="none" src={call.recording_url} className="w-full h-8 mt-1" />
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default CallHistoryPanel;

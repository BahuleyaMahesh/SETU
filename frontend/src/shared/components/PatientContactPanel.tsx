import React, { useState } from 'react';
import { useAuth } from '../../app/auth/AuthProvider';
import { Phone, MessageSquare, Navigation, MapPin, Send, X } from 'lucide-react';

interface PatientContactPanelProps {
  patientId: string;
  phone?: string;
  village?: string;
  district?: string;
  state?: string;
  address?: string;
  latitude?: number;
  longitude?: number;
}

/** Contact + registered-location card for the ASHA/hospital patient-detail
 * views — real "call", "message" and "where do they live" actions in one
 * place, next to the clinical record, instead of staff having to hunt for
 * a phone number elsewhere. Shared between ASHA and Hospital so a fix here
 * (e.g. the messaging channel logic) applies to both. */
export const PatientContactPanel: React.FC<PatientContactPanelProps> = ({
  patientId,
  phone,
  village,
  district,
  state,
  address,
  latitude,
  longitude,
}) => {
  const { token } = useAuth();
  const [composing, setComposing] = useState(false);
  const [messageText, setMessageText] = useState('');
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; text: string } | null>(null);

  const hasLocation = typeof latitude === 'number' && typeof longitude === 'number';
  const locationParts = [village, district, state].filter(Boolean).join(', ');

  const handleSend = async () => {
    if (!messageText.trim()) return;
    setSending(true);
    setResult(null);
    try {
      const res = await fetch('/api/v1/notifications/patient-message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ patient_id: patientId, message: messageText.trim() }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok && data.success !== false) {
        const channel = data.channel === 'email' ? 'email' : data.channel === 'sms' ? 'SMS' : 'the patient';
        setResult({ ok: true, text: `Message sent via ${channel}.` });
        setMessageText('');
      } else {
        setResult({ ok: false, text: data.detail || data.error || 'Could not deliver this message — try calling the patient directly instead.' });
      }
    } catch (err) {
      setResult({ ok: false, text: 'Connection issue — could not send. Try calling the patient directly instead.' });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">Contact & Registered Location</h3>

      <div className="flex flex-wrap gap-2">
        {phone && (
          <a
            href={`tel:${phone}`}
            className="inline-flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs px-3 py-2 rounded-lg"
          >
            <Phone className="w-3.5 h-3.5" />
            Call Patient ({phone})
          </a>
        )}
        <button
          onClick={() => { setComposing((c) => !c); setResult(null); }}
          className="inline-flex items-center gap-1.5 bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs px-3 py-2 rounded-lg"
        >
          <MessageSquare className="w-3.5 h-3.5" />
          Message Patient
        </button>
        {hasLocation && (
          <a
            href={`https://maps.google.com/?q=${latitude},${longitude}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 font-semibold text-xs px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700"
          >
            <Navigation className="w-3.5 h-3.5" />
            Directions
          </a>
        )}
      </div>

      {(locationParts || address || hasLocation) && (
        <div className="text-xs text-slate-600 dark:text-slate-400 flex items-start gap-1.5">
          <MapPin className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-slate-400" />
          <span>
            {address ? `${address}, ` : ''}{locationParts || 'No village/district on record'}
            {hasLocation && <span className="text-slate-400"> · {latitude!.toFixed(4)}, {longitude!.toFixed(4)}</span>}
          </span>
        </div>
      )}

      {composing && (
        <div className="p-3 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-xl space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-600 dark:text-slate-300">Send a message to this patient</span>
            <button onClick={() => setComposing(false)} className="text-slate-400 hover:text-slate-600">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
          <textarea
            rows={2}
            value={messageText}
            onChange={(e) => setMessageText(e.target.value)}
            placeholder="e.g. Please remember to take your evening medication."
            className="w-full text-sm p-2 border border-slate-300 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 rounded-lg"
          />
          <button
            onClick={handleSend}
            disabled={sending || !messageText.trim()}
            className="inline-flex items-center gap-1.5 bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs px-3 py-1.5 rounded-lg disabled:opacity-60"
          >
            <Send className="w-3.5 h-3.5" />
            {sending ? 'Sending...' : 'Send'}
          </button>
        </div>
      )}

      {result && (
        <p className={`text-xs font-medium ${result.ok ? 'text-emerald-600' : 'text-red-600'}`}>{result.text}</p>
      )}
    </div>
  );
};

export default PatientContactPanel;

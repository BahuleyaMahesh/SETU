import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../app/auth/AuthProvider';
import { Card } from '../../shared/components/Card';
import { Button } from '../../shared/components/Button';
import { Badge } from '../../shared/components/Badge';
import {
  MessageSquare,
  Send,
  Bot,
  User,
  ShieldCheck,
  Sparkles,
  PhoneCall,
  MapPin,
  AlertTriangle,
  Navigation,
  Phone,
  Building2,
  Users,
} from 'lucide-react';

interface AshaWorkerInfo {
  id?: string;
  name: string;
  phone: string;
  block?: string;
  district?: string;
  is_active?: boolean;
}

interface FacilityInfo {
  id: string;
  name: string;
  type: string;
  distance_km: number;
  phone: string;
  address: string;
  latitude: number;
  longitude: number;
}

interface PatientOption {
  id: string;
  full_name: string;
  mrn?: string;
  risk_level?: string;
}

interface ChatMessageItem {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  is_health_concern?: boolean;
  severity?: 'normal' | 'warning' | 'critical';
  asha_worker?: AshaWorkerInfo | null;
  facilities?: FacilityInfo[];
  sources?: string[];
  timestamp: Date;
}

export const StaffPatientChat: React.FC = () => {
  const { user, token } = useAuth();
  const isAsha = user?.role === 'asha';

  const [patients, setPatients] = useState<PatientOption[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState('');
  const [loadingPatients, setLoadingPatients] = useState(true);
  const [messages, setMessages] = useState<ChatMessageItem[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchPatients();
  }, [token]);

  const fetchPatients = async () => {
    if (!token) {
      setLoadingPatients(false);
      return;
    }
    setLoadingPatients(true);
    try {
      const url = isAsha && user?.asha_worker_id
        ? `/api/v1/asha/${user.asha_worker_id}/patients`
        : `/api/v1/patients`;
      const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        const data = await res.json();
        setPatients(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error('Failed to fetch patients:', err);
    } finally {
      setLoadingPatients(false);
    }
  };

  const selectedPatient = patients.find((p) => p.id === selectedPatientId);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  useEffect(scrollToBottom, [messages]);

  const handleSelectPatient = (patientId: string) => {
    setSelectedPatientId(patientId);
    setMessages([]);
  };

  // Empty selection ("All My Patients") isn't "nothing picked" — it's its
  // own mode: a roster-wide Q&A endpoint that already knows this user's
  // full authorized caseload server-side, so nothing needs to be chosen
  // first to ask "which of my patients are critical".
  const isRosterMode = !selectedPatientId;

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userQuery = input.trim();
    const userMessage: ChatMessageItem = {
      id: Date.now().toString(),
      role: 'user',
      content: userQuery,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch(isRosterMode ? '/api/v1/chat/roster-query' : '/api/v1/chat/staff-message', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(
          isRosterMode ? { message: userQuery } : { patient_id: selectedPatientId, message: userQuery }
        ),
      });

      if (response.ok) {
        const data = await response.json();
        setMessages((prev) => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: data.content || data.response || 'Logged.',
            is_health_concern: data.is_health_concern,
            severity: data.severity || 'normal',
            asha_worker: data.asha_worker,
            facilities: data.facilities || [],
            sources: data.sources || [],
            timestamp: new Date(),
          },
        ]);
      } else {
        const err = await response.json().catch(() => ({}));
        setMessages((prev) => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: err.detail || 'Could not process this report. Please try again.',
            timestamp: new Date(),
          },
        ]);
      }
    } catch (error) {
      console.error('Error in staff chat request:', error);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: 'Connection error — could not reach the server. Please try again.',
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8.5rem)] max-w-4xl mx-auto">
      {/* Top Header */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-t-2xl p-4 flex items-center justify-between shadow-sm gap-3 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-sky-50 dark:bg-sky-950 text-sky-600 dark:text-sky-400 rounded-xl">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <span>Care Assistant</span>
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950 px-2 py-0.5 rounded-full border border-emerald-200 dark:border-emerald-800">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" /> Active Safety Rules
              </span>
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {isRosterMode
                ? 'Ask about your whole caseload, or pick one patient to report symptoms'
                : "Report a patient's symptoms — deterministic rules decide risk, never the AI"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Users className="w-4 h-4 text-slate-400" />
          <select
            value={selectedPatientId}
            onChange={(e) => handleSelectPatient(e.target.value)}
            disabled={loadingPatients}
            className="text-sm px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 rounded-xl focus:outline-none focus:ring-2 focus:ring-sky-500 font-medium min-w-[200px]"
          >
            <option value="">{loadingPatients ? 'Loading patients…' : '📋 All My Patients (ask anything)'}</option>
            {patients.map((p) => (
              <option key={p.id} value={p.id}>
                {p.full_name}{p.mrn ? ` (${p.mrn})` : ''}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 bg-slate-50/90 dark:bg-slate-900/90 border-x border-slate-200 dark:border-slate-800 p-4 overflow-y-auto space-y-6">
        {isRosterMode && messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center text-slate-400 dark:text-slate-500 gap-2 px-6">
            <Users className="w-10 h-10" />
            <p className="text-sm font-medium max-w-sm">
              Ask anything about your patient list — e.g. "which patients are critical right now",
              "when did Ramesh last check in", or "who's in Whitefield".
            </p>
            <p className="text-xs">Or pick one patient above to report their symptoms directly.</p>
          </div>
        ) : (
          <>
            {!isRosterMode && (
              <div className="text-center text-xs text-slate-400 dark:text-slate-500 font-medium">
                Reporting on <span className="text-slate-700 dark:text-slate-300 font-bold">{selectedPatient?.full_name}</span>
              </div>
            )}
            {messages.map((msg) => {
              const isUser = msg.role === 'user';
              const isHealthConcern = msg.is_health_concern;
              const isCritical = msg.severity === 'critical';

              return (
                <div key={msg.id} className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs shadow-sm flex-shrink-0 ${
                    isUser ? 'bg-sky-600 text-white' : 'bg-teal-600 text-white'
                  }`}>
                    {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </div>

                  <div className={`w-full max-w-[92%] sm:max-w-[82%] space-y-3 ${isUser ? 'items-end' : 'items-start'}`}>
                    {!isUser && isHealthConcern ? (
                      <div className={`p-4 rounded-2xl border transition-all ${
                        isCritical
                          ? 'bg-red-50 dark:bg-red-950/40 border-red-300 dark:border-red-800 text-red-950 dark:text-red-100 shadow-md shadow-red-500/10'
                          : 'bg-amber-50/90 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800 text-amber-950 dark:text-amber-100 shadow-sm'
                      }`}>
                        <div className="flex items-center justify-between border-b border-slate-200/60 dark:border-slate-700/60 pb-2 mb-3">
                          <div className="flex items-center gap-2 font-black text-sm uppercase tracking-wider">
                            <AlertTriangle className={`w-4 h-4 ${isCritical ? 'text-red-600 dark:text-red-400' : 'text-amber-600 dark:text-amber-400'}`} />
                            <span>{isCritical ? 'CRITICAL RISK' : 'ELEVATED RISK'}</span>
                          </div>
                          <Badge variant={isCritical ? 'danger' : 'warning'}>
                            {isCritical ? 'URGENT' : 'MONITOR'}
                          </Badge>
                        </div>

                        <div className="text-sm leading-relaxed whitespace-pre-wrap font-medium">
                          {msg.content}
                        </div>

                        {msg.asha_worker && msg.asha_worker.phone && (
                          <div className="mt-4 pt-3 border-t border-slate-200/80 dark:border-slate-700/80">
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white dark:bg-slate-900 p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                              <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-teal-50 dark:bg-teal-950 border border-teal-200 dark:border-teal-800 rounded-xl flex items-center justify-center text-teal-700 dark:text-teal-400 font-bold">
                                  <PhoneCall className="w-5 h-5" />
                                </div>
                                <div>
                                  <div className="text-xs text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider">Assigned ASHA</div>
                                  <div className="font-bold text-slate-900 dark:text-slate-100 text-sm">{msg.asha_worker.name}</div>
                                  <div className="text-xs text-slate-500 dark:text-slate-400">{msg.asha_worker.block} • {msg.asha_worker.phone}</div>
                                </div>
                              </div>
                              <a
                                href={`tel:${msg.asha_worker.phone}`}
                                className="bg-teal-700 hover:bg-teal-600 text-white font-bold text-xs py-2.5 px-4 rounded-xl inline-flex items-center gap-1.5 shadow-sm"
                              >
                                <Phone className="w-3.5 h-3.5" />
                                <span>Call</span>
                              </a>
                            </div>
                          </div>
                        )}

                        {msg.facilities && msg.facilities.length > 0 && (
                          <div className="mt-4 pt-3 border-t border-slate-200/80 dark:border-slate-700/80">
                            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-1.5 mb-2.5">
                              <Building2 className="w-4 h-4 text-sky-600 dark:text-sky-400" />
                              <span>NEAREST HOSPITAL TO PATIENT</span>
                            </h4>
                            <div className="grid gap-2.5">
                              {msg.facilities.map((fac) => (
                                <div key={fac.id} className="bg-white dark:bg-slate-900 p-3.5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                                  <div>
                                    <div className="flex items-center gap-2">
                                      <span className="font-bold text-slate-900 dark:text-slate-100 text-sm">{fac.name}</span>
                                      <span className="text-[10px] font-bold uppercase px-2 py-0.5 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-md border border-slate-200 dark:border-slate-700">
                                        {fac.type}
                                      </span>
                                    </div>
                                    <div className="text-xs text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-3">
                                      <span>📍 {fac.address}</span>
                                      <span className="font-semibold text-sky-600 dark:text-sky-400">~{fac.distance_km} km away</span>
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <a
                                      href={`https://maps.google.com/?q=${fac.latitude},${fac.longitude}`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 font-semibold text-xs rounded-lg inline-flex items-center gap-1 border border-slate-200 dark:border-slate-700"
                                    >
                                      <Navigation className="w-3.5 h-3.5 text-sky-600 dark:text-sky-400" />
                                      <span>Directions</span>
                                    </a>
                                    <a
                                      href={`tel:${fac.phone}`}
                                      className="px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs rounded-lg inline-flex items-center gap-1 shadow-sm"
                                    >
                                      <Phone className="w-3.5 h-3.5" />
                                      <span>Call</span>
                                    </a>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className={`p-4 rounded-2xl text-sm leading-relaxed ${
                        isUser
                          ? 'bg-sky-600 text-white rounded-tr-none shadow-md shadow-sky-600/10'
                          : 'bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 border border-slate-200/80 dark:border-slate-700/80 rounded-tl-none shadow-sm'
                      }`}>
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                        {msg.sources && msg.sources.length > 0 && (
                          <div className="mt-3 pt-2 border-t border-slate-100 dark:border-slate-700 flex items-center gap-1.5 text-[11px] text-teal-700 dark:text-teal-400 font-medium">
                            <Sparkles className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
                            <span>Verified sources: {msg.sources.join(', ')}</span>
                          </div>
                        )}
                      </div>
                    )}

                    <span className={`text-[10px] text-slate-400 dark:text-slate-500 block px-1 ${isUser ? 'text-right' : 'text-left'}`}>
                      {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>
              );
            })}
          </>
        )}

        {loading && (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-teal-600 text-white rounded-xl flex items-center justify-center">
              <Bot className="w-4 h-4 animate-spin" />
            </div>
            <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl rounded-tl-none p-3.5 text-xs text-slate-600 dark:text-slate-300 flex items-center gap-2 shadow-sm">
              <div className="w-2 h-2 bg-teal-500 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-teal-500 rounded-full animate-bounce [animation-delay:0.2s]" />
              <div className="w-2 h-2 bg-teal-500 rounded-full animate-bounce [animation-delay:0.4s]" />
              <span>Checking safety rules & nearest facilities…</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-b-2xl p-3 shadow-sm">
        <form onSubmit={handleSend} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isRosterMode ? 'Ask about your patient list…' : "Describe the patient's symptoms or condition…"}
            className="flex-1 px-4 py-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 text-slate-800 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500"
            disabled={loading}
          />
          <Button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-sky-600 hover:bg-sky-500 text-white font-bold px-5 py-3 rounded-xl transition-all shadow-md shadow-sky-600/20 text-sm flex items-center gap-1.5"
          >
            <Send className="w-4 h-4" />
            <span className="hidden sm:inline">Send</span>
          </Button>
        </form>
      </div>
    </div>
  );
};

export default StaffPatientChat;

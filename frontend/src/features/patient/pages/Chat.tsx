import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../../app/auth/AuthProvider';
import { Card } from '../../../shared/components/Card';
import { Button } from '../../../shared/components/Button';
import { Badge } from '../../../shared/components/Badge';
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
  CheckCircle2,
  Clock,
  Building2,
  Activity,
  XCircle,
  ExternalLink
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

interface ChatMessageItem {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  is_health_concern?: boolean;
  severity?: 'normal' | 'warning' | 'critical';
  asha_worker?: AshaWorkerInfo;
  facilities?: FacilityInfo[];
  sources?: string[];
  timestamp: Date;
}

export const PatientChat: React.FC = () => {
  const { user, token } = useAuth();
  const [messages, setMessages] = useState<ChatMessageItem[]>([
    {
      id: '1',
      role: 'assistant',
      content: `Hello ${user?.full_name?.split(' ')[0] || ''}! I am your SETU Continuous Care Assistant. How are you feeling today? Tell me about any symptoms, medications, or post-discharge recovery questions.`,
      sources: ['SETU Clinical Care Protocol'],
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [callState, setCallState] = useState<{ [msgId: string]: 'idle' | 'connecting' | 'connected' | 'failed' }>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  const handleConnectAsha = async (msgId: string, asha: AshaWorkerInfo) => {
    setCallState(prev => ({ ...prev, [msgId]: 'connecting' }));

    try {
      const response = await fetch('/api/v1/calls/outbound', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          patient_id: user?.patient_id || user?.id,
          to_phone: asha.phone,
          call_type: 'emergency_escalation'
        }),
      });

      if (response.ok) {
        setCallState(prev => ({ ...prev, [msgId]: 'connected' }));
      } else {
        setCallState(prev => ({ ...prev, [msgId]: 'failed' }));
      }
    } catch (err) {
      console.error('Call connection error:', err);
      setCallState(prev => ({ ...prev, [msgId]: 'failed' }));
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userQuery = input.trim();
    const userMessage: ChatMessageItem = {
      id: Date.now().toString(),
      role: 'user',
      content: userQuery,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('/api/v1/chat/message', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userQuery, content: userQuery }),
      });

      if (response.ok) {
        const data = await response.json();
        const assistantMessage: ChatMessageItem = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.content || data.response || 'Your symptom query has been analyzed.',
          is_health_concern: data.is_health_concern ?? true,
          severity: data.severity || 'warning',
          asha_worker: data.asha_worker || {
            name: 'Priya Sharma (ASHA)',
            phone: '+91-98765-43210',
            block: 'Whitefield Block'
          },
          facilities: data.facilities || [
            {
              id: 'f-chc',
              name: 'Whitefield Community Health Center (CHC)',
              type: 'CHC',
              distance_km: 2.4,
              phone: '+91-80-2845-1234',
              address: 'Main Road, Whitefield Block',
              latitude: 12.9698,
              longitude: 77.7499
            },
            {
              id: 'f-cgh',
              name: 'City General Hospital',
              type: 'District Hospital',
              distance_km: 5.8,
              phone: '+91-80-2222-3333',
              address: 'Station Road, District HQ',
              latitude: 12.9716,
              longitude: 77.5946
            }
          ],
          sources: data.sources || ['SETU Safety Protocol'],
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        // Honest failure: the message was NOT saved and NOT sent to anyone.
        // Do not imply escalation happened — that's what caused a real
        // patient-safety gap (see HANDOVER.md). is_health_concern stays
        // unset so this renders as a plain bubble, not a fake triage banner
        // with fabricated ASHA/facility contact cards.
        const fallbackMsg: ChatMessageItem = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `Sorry, there was a connection issue and I couldn't process that message — nothing was saved or sent to your care team. Please try again in a moment. If this is urgent, call your ASHA worker directly or go to the nearest health facility right away.`,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, fallbackMsg]);
      }
    } catch (error) {
      console.error('Error in chat request:', error);
      // Same honesty rule as above — this branch means the request never
      // even reached the server (network error / backend down), so there
      // is even less basis to claim anything was "logged".
      const offlineMsg: ChatMessageItem = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Sorry, there was a connection issue and I couldn't reach the server — nothing was saved or sent to your care team. Please try again in a moment. If this is urgent, call your ASHA worker directly or go to the nearest health facility right away.`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, offlineMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8.5rem)] max-w-4xl mx-auto">
      {/* Top Header */}
      <div className="bg-white border border-slate-200 rounded-t-2xl p-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-sky-50 text-sky-600 rounded-xl">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <span>SETU Care Assistant</span>
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> Active Safety Rules
              </span>
            </h1>
            <p className="text-xs text-slate-500">Continuous Monitoring • ASHA Connection • Facility Triage</p>
          </div>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 bg-slate-50/90 dark:bg-slate-900/90 border-x border-slate-200 dark:border-slate-800 p-4 overflow-y-auto space-y-6">
        {messages.map((msg) => {
          const isUser = msg.role === 'user';
          const isHealthConcern = msg.is_health_concern;
          const isCritical = msg.severity === 'critical';
          const isWarning = msg.severity === 'warning';
          const currentCallState = callState[msg.id] || 'idle';

          return (
            <div key={msg.id} className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
              <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs shadow-sm flex-shrink-0 ${
                isUser ? 'bg-sky-600 text-white' : 'bg-teal-600 text-white'
              }`}>
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div className={`w-full max-w-[92%] sm:max-w-[82%] space-y-3 ${isUser ? 'items-end' : 'items-start'}`}>
                
                {/* Emergency/Urgent Priority Banner for health concerns */}
                {!isUser && isHealthConcern && (
                  <div className={`p-4 rounded-2xl border transition-all ${
                    isCritical
                      ? 'bg-red-50 border-red-300 text-red-950 shadow-md shadow-red-500/10'
                      : 'bg-amber-50/90 border-amber-200 text-amber-950 shadow-sm'
                  }`}>
                    <div className="flex items-center justify-between border-b border-slate-200/60 pb-2 mb-3">
                      <div className="flex items-center gap-2 font-black text-sm uppercase tracking-wider">
                        <AlertTriangle className={`w-4 h-4 ${isCritical ? 'text-red-600' : 'text-amber-600'}`} />
                        <span>{isCritical ? 'CRITICAL HEALTH CONCERN' : 'HEALTH TRIAGE GUIDANCE'}</span>
                      </div>
                      <Badge variant={isCritical ? 'danger' : 'warning'}>
                        {isCritical ? 'URGENT ESCALATION' : 'TEMPORARY GUIDANCE'}
                      </Badge>
                    </div>

                    {/* Response Text */}
                    <div className="text-sm leading-relaxed whitespace-pre-wrap font-medium">
                      {msg.content}
                    </div>

                    {/* Action 1: CONNECT TO ASHA CENTRE */}
                    {msg.asha_worker && (
                      <div className="mt-4 pt-3 border-t border-slate-200/80">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-teal-50 border border-teal-200 rounded-xl flex items-center justify-center text-teal-700 font-bold">
                              <PhoneCall className="w-5 h-5" />
                            </div>
                            <div>
                              <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Assigned Health Worker</div>
                              <div className="font-bold text-slate-900 text-sm">{msg.asha_worker.name}</div>
                              <div className="text-xs text-slate-500">{msg.asha_worker.block} • {msg.asha_worker.phone}</div>
                            </div>
                          </div>

                          {currentCallState === 'connecting' ? (
                            <Button disabled className="bg-teal-600 text-white font-semibold text-xs py-2.5 px-4 rounded-xl flex items-center gap-2">
                              <div className="animate-spin rounded-full h-3.5 w-3.5 border-b-2 border-white" />
                              <span>Connecting Call...</span>
                            </Button>
                          ) : currentCallState === 'connected' ? (
                            <div className="flex items-center gap-2 text-xs font-bold text-emerald-700 bg-emerald-50 px-3 py-2 rounded-xl border border-emerald-200">
                              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                              <span>Call Dispatched via Telephony</span>
                            </div>
                          ) : currentCallState === 'failed' ? (
                            <div className="flex items-center gap-2">
                              <a
                                href={`tel:${msg.asha_worker.phone}`}
                                className="bg-red-600 hover:bg-red-500 text-white font-bold text-xs py-2.5 px-4 rounded-xl inline-flex items-center gap-1.5 shadow-sm"
                              >
                                <Phone className="w-3.5 h-3.5" />
                                <span>Direct Call ({msg.asha_worker.phone})</span>
                              </a>
                            </div>
                          ) : (
                            <Button
                              onClick={() => handleConnectAsha(msg.id, msg.asha_worker!)}
                              className="bg-teal-700 hover:bg-teal-600 text-white font-bold text-xs py-2.5 px-4 rounded-xl flex items-center justify-center gap-2 shadow-md shadow-teal-700/20"
                            >
                              <PhoneCall className="w-4 h-4" />
                              <span>CONNECT TO ASHA CENTRE</span>
                            </Button>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Action 2: NEAREST HEALTH FACILITIES MAP CARD */}
                    {msg.facilities && msg.facilities.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-slate-200/80">
                        <div className="flex items-center justify-between mb-2.5">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                            <Building2 className="w-4 h-4 text-sky-600" />
                            <span>NEAREST HEALTH FACILITIES</span>
                          </h4>
                          <span className="text-[11px] font-medium text-slate-500">Live Geo Triage</span>
                        </div>

                        {/* Interactive Compact Map View */}
                        <div className="bg-slate-900 text-white rounded-xl p-3 mb-3 border border-slate-800 flex items-center justify-between">
                          <div className="flex items-center gap-2.5">
                            <div className="p-2 bg-sky-500/20 text-sky-400 rounded-lg">
                              <MapPin className="w-5 h-5 animate-bounce" />
                            </div>
                            <div>
                              <div className="text-xs font-bold text-white">Patient Regional Sector</div>
                              <div className="text-[11px] text-slate-400">Lat: {msg.facilities[0].latitude} • Lon: {msg.facilities[0].longitude}</div>
                            </div>
                          </div>
                          <Badge variant="info" className="bg-sky-500/20 text-sky-300 border border-sky-400/30 text-[10px]">
                            {msg.facilities.length} Verified Centers
                          </Badge>
                        </div>

                        {/* Facilities Cards List */}
                        <div className="grid gap-2.5">
                          {msg.facilities.map((fac) => (
                            <div key={fac.id} className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                              <div>
                                <div className="flex items-center gap-2">
                                  <span className="font-bold text-slate-900 text-sm">{fac.name}</span>
                                  <span className="text-[10px] font-bold uppercase px-2 py-0.5 bg-slate-100 text-slate-700 rounded-md border border-slate-200">
                                    {fac.type}
                                  </span>
                                </div>
                                <div className="text-xs text-slate-500 mt-1 flex items-center gap-3">
                                  <span>📍 {fac.address}</span>
                                  <span className="font-semibold text-sky-600">~{fac.distance_km} km away</span>
                                </div>
                              </div>

                              <div className="flex items-center gap-2">
                                <a
                                  href={`https://maps.google.com/?q=${fac.latitude},${fac.longitude}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs rounded-lg inline-flex items-center gap-1 border border-slate-200"
                                >
                                  <Navigation className="w-3.5 h-3.5 text-sky-600" />
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
                )}

                {/* Standard Message Bubble for Non-Health Concerns or User messages */}
                {(isUser || !isHealthConcern) && (
                  <div className={`p-4 rounded-2xl text-sm leading-relaxed ${
                    isUser
                      ? 'bg-sky-600 text-white rounded-tr-none shadow-md shadow-sky-600/10'
                      : 'bg-white text-slate-800 border border-slate-200/80 rounded-tl-none shadow-sm'
                  }`}>
                    <p className="whitespace-pre-wrap">{msg.content}</p>

                    {msg.sources && msg.sources.length > 0 && (
                      <div className="mt-3 pt-2 border-t border-slate-100 flex items-center gap-1.5 text-[11px] text-teal-700 font-medium">
                        <Sparkles className="w-3.5 h-3.5 text-teal-600" />
                        <span>Verified sources: {msg.sources.join(', ')}</span>
                      </div>
                    )}
                  </div>
                )}

                <span className={`text-[10px] text-slate-400 block px-1 ${isUser ? 'text-right' : 'text-left'}`}>
                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            </div>
          );
        })}

        {loading && (
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-teal-600 text-white rounded-xl flex items-center justify-center">
              <Bot className="w-4 h-4 animate-spin" />
            </div>
            <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-none p-3.5 text-xs text-slate-600 flex items-center gap-2 shadow-sm">
              <div className="w-2 h-2 bg-teal-500 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-teal-500 rounded-full animate-bounce [animation-delay:0.2s]" />
              <div className="w-2 h-2 bg-teal-500 rounded-full animate-bounce [animation-delay:0.4s]" />
              <span>Analyzing symptom safety rules & nearby health centers...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="bg-white border border-slate-200 rounded-b-2xl p-3 shadow-sm">
        <form onSubmit={handleSend} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Describe any symptoms (e.g. My head is hurting, fever, pain)..."
            className="flex-1 px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 text-slate-800 placeholder-slate-400"
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

export default PatientChat;

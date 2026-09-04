import React, { useState } from 'react';
import { useAuth } from '../../../app/auth/AuthProvider';
import { Card } from '../../../shared/components/Card';
import { Button } from '../../../shared/components/Button';
import { Badge } from '../../../shared/components/Badge';
import { Activity, AlertTriangle, CheckCircle2, RotateCcw, Send } from 'lucide-react';

export const PatientCheckup: React.FC = () => {
  const { user, token } = useAuth();
  const [symptoms, setSymptoms] = useState<string[]>([]);
  const [severity, setSeverity] = useState(3);
  const [voiceText, setVoiceText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const commonSymptoms = [
    'Fever / Chills',
    'Headache',
    'Shortness of Breath',
    'Chest Discomfort',
    'Abdominal Pain',
    'Severe Fatigue',
    'Dizziness',
    'Vomiting / Nausea',
  ];

  const handleSymptomToggle = (symptom: string) => {
    setSymptoms(prev =>
      prev.includes(symptom)
        ? prev.filter(s => s !== symptom)
        : [...prev, symptom]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Primary Endpoint: /api/v1/checkins
      const response = await fetch('/api/v1/checkins', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          method: 'web',
          input_type: voiceText ? 'voice' : 'text',
          raw_input: voiceText || symptoms.join(', '),
          responses: {
            symptoms,
            severity,
          },
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setResult(data);
      } else {
        // Fallback to /api/v1/risk/evaluate if checkins has different parameters
        const fallbackRes = await fetch('/api/v1/risk/evaluate', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ symptoms, severity }),
        });
        const fallbackData = await fallbackRes.json();
        setResult(fallbackData);
      }
    } catch (error) {
      console.error('Error submitting check-in:', error);
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    const riskLevel = result.risk_level || result.evaluation?.risk_level || 'normal';
    const isCritical = riskLevel === 'critical';
    const isWarning = riskLevel === 'warning';

    return (
      <div className="space-y-6">
        <Card className="p-6">
          <div className="flex items-center justify-between border-b border-slate-200 pb-4 mb-6">
            <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
              <Activity className="w-5 h-5 text-sky-600" />
              <span>Check-in Assessment Result</span>
            </h2>
            <Badge variant={isCritical ? 'danger' : isWarning ? 'warning' : 'success'}>
              {riskLevel.toUpperCase()} RISK
            </Badge>
          </div>

          {/* Risk Level Banner */}
          <div className={`p-5 rounded-2xl mb-6 border ${
            isCritical ? 'bg-red-50 border-red-200 text-red-900' :
            isWarning ? 'bg-amber-50 border-amber-200 text-amber-900' :
            'bg-emerald-50 border-emerald-200 text-emerald-900'
          }`}>
            <div className="flex items-start gap-3">
              {isCritical ? (
                <AlertTriangle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
              ) : (
                <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-0.5" />
              )}
              <div>
                <h3 className="font-bold text-lg">
                  {isCritical ? 'Urgent Action Recommended' : isWarning ? 'Moderate Care Guidance' : 'Normal Health Status'}
                </h3>
                <p className="text-sm mt-1 leading-relaxed opacity-90">
                  {result.action_required || result.recommendations?.[0] || 'Your check-in data has been logged and synchronized with your assigned ASHA worker.'}
                </p>
              </div>
            </div>
          </div>

          {/* Reported Symptoms */}
          <div className="space-y-4 mb-6">
            <div>
              <h4 className="text-sm font-semibold text-slate-700 uppercase tracking-wider mb-2">Reported Symptoms</h4>
              <div className="flex flex-wrap gap-2">
                {(result.risk_factors || symptoms).map((s: string) => (
                  <span key={s} className="px-3 py-1 bg-slate-100 border border-slate-200 text-slate-800 rounded-lg text-sm font-medium">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <Button
            onClick={() => {
              setResult(null);
              setSymptoms([]);
              setVoiceText('');
            }}
            className="w-full bg-slate-800 hover:bg-slate-700 text-white font-semibold py-3 rounded-xl flex items-center justify-center gap-2"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Submit Another Check-in</span>
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="border-b border-slate-200 pb-4 mb-6">
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Daily Health Check-in</h2>
          <p className="text-sm text-slate-500 mt-1">Select any symptoms you are currently experiencing to evaluate risk.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Symptoms Grid */}
          <div>
            <label className="block text-sm font-semibold text-slate-800 mb-3">
              1. Are you experiencing any of these symptoms today?
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {commonSymptoms.map(symptom => {
                const isSelected = symptoms.includes(symptom);
                return (
                  <button
                    key={symptom}
                    type="button"
                    onClick={() => handleSymptomToggle(symptom)}
                    className={`p-3.5 rounded-xl border text-left text-sm font-medium transition-all duration-200 flex items-center justify-between ${
                      isSelected
                        ? 'border-sky-600 bg-sky-50 text-sky-800 shadow-sm font-semibold'
                        : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                    }`}
                  >
                    <span>{symptom}</span>
                    {isSelected && <CheckCircle2 className="w-4 h-4 text-sky-600" />}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Voice Input Box */}
          <div>
            <label className="block text-sm font-semibold text-slate-800 mb-2">
              2. Optional Voice / Additional Notes
            </label>
            <textarea
              value={voiceText}
              onChange={(e) => setVoiceText(e.target.value)}
              placeholder="Type or dictate additional details about how you feel today..."
              rows={3}
              className="w-full p-3.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 placeholder-slate-400"
            />
          </div>

          {/* Severity Slider */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="text-sm font-semibold text-slate-800">
                3. Overall Discomfort Level
              </label>
              <span className="text-sm font-bold text-sky-600 bg-sky-50 px-2.5 py-0.5 rounded-lg border border-sky-200">
                {severity} / 10
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="10"
              value={severity}
              onChange={(e) => setSeverity(parseInt(e.target.value))}
              className="w-full accent-sky-600 cursor-pointer"
            />
            <div className="flex justify-between text-xs text-slate-400 mt-1">
              <span>Mild (1)</span>
              <span>Moderate (5)</span>
              <span>Severe (10)</span>
            </div>
          </div>

          <Button
            type="submit"
            disabled={loading || (symptoms.length === 0 && !voiceText)}
            isLoading={loading}
            className="w-full bg-sky-600 hover:bg-sky-500 text-white font-semibold py-3.5 rounded-xl shadow-lg shadow-sky-600/20 text-sm flex items-center justify-center gap-2"
          >
            <Send className="w-4 h-4" />
            <span>{loading ? 'Evaluating Risk...' : 'Submit Health Check-in'}</span>
          </Button>
        </form>
      </Card>
    </div>
  );
};

export default PatientCheckup;

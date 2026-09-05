import React from 'react';
import { TrendingDown, TrendingUp, Minus } from 'lucide-react';

interface RiskHistoryEntry {
  id: string;
  risk_level: string;
  risk_score?: number;
  severity?: number;
  created_at: string;
  risk_reasons?: string[];
}

interface RiskHistoryTimelineProps {
  history?: RiskHistoryEntry[];
}

const RISK_RANK: Record<string, number> = { normal: 0, warning: 1, critical: 2 };

const riskColor = (level: string) =>
  level === 'critical'
    ? 'bg-red-100 text-red-700 border-red-200'
    : level === 'warning'
    ? 'bg-amber-100 text-amber-700 border-amber-200'
    : 'bg-emerald-100 text-emerald-700 border-emerald-200';

/** Chronological log of a patient's risk-level changes — the "symptoms and
 * improvements over time" view ASHA/hospital staff need, distinct from the
 * raw combined-symptoms list (which shows individual reported observations,
 * not the trend). Backend already returns this as `risk_history` (newest
 * first) on the same GET /api/v1/patients/{id} call that supplies
 * combined_symptoms/latest_risk — no separate fetch needed here. */
export const RiskHistoryTimeline: React.FC<RiskHistoryTimelineProps> = ({ history }) => {
  if (!history || history.length === 0) {
    return <p className="text-xs text-slate-500 italic">No risk history recorded yet.</p>;
  }

  return (
    <div className="space-y-2">
      {history.slice(0, 8).map((entry, idx) => {
        const older = history[idx + 1];
        const rank = RISK_RANK[entry.risk_level] ?? 0;
        const olderRank = older ? RISK_RANK[older.risk_level] ?? 0 : null;
        const trend = olderRank === null ? null : rank < olderRank ? 'down' : rank > olderRank ? 'up' : 'flat';

        return (
          <div key={entry.id} className="flex items-start gap-2.5 text-xs">
            <div className="flex flex-col items-center pt-0.5">
              {trend === 'down' && <TrendingDown className="w-3.5 h-3.5 text-emerald-600" />}
              {trend === 'up' && <TrendingUp className="w-3.5 h-3.5 text-red-600" />}
              {(trend === 'flat' || trend === null) && <Minus className="w-3.5 h-3.5 text-slate-300" />}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`px-2 py-0.5 rounded-full font-bold uppercase text-[10px] border ${riskColor(entry.risk_level)}`}>
                  {entry.risk_level}
                </span>
                <span className="text-slate-400">
                  {new Date(entry.created_at).toLocaleString(undefined, {
                    month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
                  })}
                </span>
                {trend === 'down' && <span className="text-emerald-600 font-semibold">Improved</span>}
                {trend === 'up' && <span className="text-red-600 font-semibold">Worsened</span>}
              </div>
              {entry.risk_reasons && entry.risk_reasons.length > 0 && (
                <p className="text-slate-500 dark:text-slate-400 mt-0.5">{entry.risk_reasons.join('; ')}</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default RiskHistoryTimeline;

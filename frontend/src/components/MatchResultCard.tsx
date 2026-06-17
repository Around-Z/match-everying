'use client';

import { useState } from 'react';

interface MatchResultItem {
  submission_id: string;
  matched_submission_id: string;
  similarity_score: number;
  matched_user_name: string;
  matched_form_data: Record<string, any>;
  explanation: string;
}

interface Props {
  match: MatchResultItem;
  rank: number;
  displayFields?: string[];
}

const CONTACT_HIDDEN_MARKER = '***';

export default function MatchResultCard({ match, rank, displayFields }: Props) {
  const [expanded, setExpanded] = useState(false);
  const scorePercent = Math.round(match.similarity_score * 100);

  // Score tier
  const tier =
    scorePercent >= 85 ? { label: '极佳匹配', color: 'from-emerald-400 to-green-500', bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' }
    : scorePercent >= 70 ? { label: '高度匹配', color: 'from-blue-400 to-indigo-500', bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' }
    : scorePercent >= 50 ? { label: '良好匹配', color: 'from-amber-400 to-orange-500', bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' }
    : { label: '一般匹配', color: 'from-gray-300 to-gray-400', bg: 'bg-gray-50', text: 'text-gray-500', border: 'border-gray-200' };

  const formData = match.matched_form_data || {};
  const contactKey = Object.keys(formData).find(k => k === 'contact' || k === '联系方式');
  const contactValue = contactKey ? formData[contactKey] : null;
  const isContactHidden = typeof contactValue === 'string' && contactValue.includes(CONTACT_HIDDEN_MARKER);

  // Sort fields: contact first (if visible), then the rest
  const fieldEntries = Object.entries(formData);
  const contactEntry = fieldEntries.find(([k]) => k === contactKey);
  const otherEntries = fieldEntries.filter(([k]) => k !== contactKey && k !== 'name');

  // Avatar from name
  const displayName = match.matched_user_name || '匿名用户';
  const avatarLetter = displayName.charAt(0).toUpperCase();

  return (
    <div className={`bg-white rounded-2xl border ${tier.border} overflow-hidden card-lift transition-all duration-300`}>
      {/* Score bar at top */}
      <div className="h-1.5 bg-gray-100">
        <div
          className={`h-full bg-gradient-to-r ${tier.color} transition-all duration-700 ease-out`}
          style={{ width: `${scorePercent}%` }}
        />
      </div>

      <div className="p-5">
        {/* Header: Avatar + Name + Score */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${tier.color} flex items-center justify-center text-white font-bold text-lg shadow-sm`}>
              {avatarLetter}
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 text-base">{displayName}</h3>
              <p className="text-xs text-gray-400">#{rank} 匹配</p>
            </div>
          </div>
          <div className="text-right">
            <div className={`text-xl font-bold ${tier.text}`}>{scorePercent}%</div>
            <span className={`text-xs px-2 py-0.5 rounded-full ${tier.bg} ${tier.text}`}>{tier.label}</span>
          </div>
        </div>

        {/* Contact field — ALWAYS first and prominent */}
        {contactEntry && (
          <div className={`rounded-xl p-3 mb-3 border ${isContactHidden ? 'bg-gray-50 border-gray-200' : 'bg-green-50 border-green-200'}`}>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-base">{isContactHidden ? '🔒' : '📞'}</span>
              <span className="text-xs font-medium text-gray-500">联系方式</span>
            </div>
            {isContactHidden ? (
              <div className="text-sm text-gray-400 italic">
                匹配度不足 50%，联系方式已隐藏。提高匹配度后可查看。
              </div>
            ) : (
              <div className="text-sm font-semibold text-green-800">
                {String(contactValue)}
              </div>
            )}
          </div>
        )}

        {/* Other form data — grid */}
        <div className="grid grid-cols-2 gap-2 mb-3">
          {otherEntries.slice(0, expanded ? otherEntries.length : 6).map(([key, value]) => (
            <div key={key} className="bg-gray-50 rounded-lg px-3 py-2">
              <span className="text-xs text-gray-400">{key}</span>
              <p className="text-sm font-medium text-gray-800 break-words">
                {Array.isArray(value) ? value.join(', ') : String(value ?? '-')}
              </p>
            </div>
          ))}
        </div>

        {/* Expand button for long data */}
        {otherEntries.length > 6 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-indigo-600 hover:text-indigo-700 font-medium mb-3"
          >
            {expanded ? '收起' : `查看全部 ${otherEntries.length} 项 →`}
          </button>
        )}

        {/* AI Explanation */}
        {match.explanation && (
          <details className="group">
            <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700 py-1">
              🤖 AI 匹配分析
            </summary>
            <div className="mt-2 text-xs text-gray-600 whitespace-pre-line leading-relaxed bg-gray-50 rounded-lg p-3 border border-gray-100">
              {match.explanation}
            </div>
          </details>
        )}

        {/* Contact CTA — when contact is visible */}
        {contactEntry && !isContactHidden && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <p className="text-xs text-gray-500 mb-2">
              💡 这是你的匹配对象，通过上方联系方式即可取得联系
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

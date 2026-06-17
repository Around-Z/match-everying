'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth';
import { apiGet } from '@/lib/api';

interface Submission {
  id: string;
  scenario_id: string;
  scenario_name: string;
  scenario_status: string;
  form_data: Record<string, any>;
  created_at: string;
}

interface MatchItem {
  id: string;
  submission_id: string;
  matched_submission_id: string;
  similarity_score: number;
  explanation: string;
  matched_form_data: Record<string, any>;
  scenario_id: string;
  scenario_name: string;
  matched_user_name: string;
}

const CONTACT_HIDDEN_MARKER = '***';

export default function UserDashboardPage() {
  const { user, isAuthenticated, loading: authLoading, updateProfile, refreshUser } = useAuth();
  const router = useRouter();
  const [tab, setTab] = useState<'profile' | 'submissions' | 'matches'>('matches');
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [matches, setMatches] = useState<MatchItem[]>([]);
  const [loading, setLoading] = useState(false);

  // Profile editing state
  const [editingProfile, setEditingProfile] = useState(false);
  const [editContact, setEditContact] = useState('');
  const [editTags, setEditTags] = useState('');
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileError, setProfileError] = useState('');

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push('/login');
  }, [authLoading, isAuthenticated]);

  useEffect(() => {
    if (!isAuthenticated) return;
    if (tab === 'submissions') fetchSubmissions();
    if (tab === 'matches') fetchMatches();
  }, [tab, isAuthenticated]);

  const fetchSubmissions = async () => {
    setLoading(true);
    try {
      const data = await apiGet('/auth/me/submissions');
      setSubmissions(data.submissions || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const fetchMatches = async () => {
    setLoading(true);
    try {
      const data = await apiGet('/auth/me/matches');
      setMatches(data.matches || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  if (authLoading || !user) {
    return (
      <div className="max-w-xl mx-auto text-center py-16">
        <div className="w-16 h-16 mx-auto mb-4 relative">
          <div className="absolute inset-0 bg-indigo-100 rounded-full animate-ping opacity-75"></div>
          <div className="relative w-16 h-16 bg-indigo-600 rounded-full flex items-center justify-center">
            <svg className="animate-spin h-8 w-8 text-white" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
            </svg>
          </div>
        </div>
        <p className="text-gray-500">加载中...</p>
      </div>
    );
  }

  const groupedSubmissions: Record<string, Submission[]> = {};
  submissions.forEach(s => {
    const key = s.scenario_id || 'unknown';
    if (!groupedSubmissions[key]) groupedSubmissions[key] = [];
    groupedSubmissions[key].push(s);
  });

  const tabs = [
    { key: 'matches' as const, label: `我的匹配 (${matches.length})`, icon: '🎯' },
    { key: 'submissions' as const, label: `我的提交 (${submissions.length})`, icon: '📝' },
    { key: 'profile' as const, label: '个人资料', icon: '👤' },
  ];

  return (
    <div className="max-w-4xl mx-auto animate-fade-in">
      {/* Profile Header */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-6 shadow-sm">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center text-white font-bold text-xl shadow-sm">
            {user.username.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1">
            <h1 className="text-xl font-bold text-gray-900">{user.username}</h1>
            <p className="text-gray-500 text-sm">{user.email}</p>
          </div>
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
            user.role === 'admin' ? 'bg-red-100 text-red-700'
            : user.role === 'designer' ? 'bg-indigo-100 text-indigo-700'
            : 'bg-green-100 text-green-700'
          }`}>
            {user.role === 'admin' ? '管理员' : user.role === 'designer' ? '场景设计者' : '参与者'}
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-xl p-1.5 mb-6">
        {tabs.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 flex items-center justify-center gap-1.5 ${
              tab === t.key ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
            }`}>
            <span>{t.icon}</span> {t.label}
          </button>
        ))}
      </div>

      {/* Profile Tab — Editable */}
      {tab === 'profile' && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          {!editingProfile ? (
            <div>
              <dl className="divide-y divide-gray-100 mb-4">
                <div className="flex justify-between py-3"><dt className="text-gray-500 text-sm">用户 ID</dt><dd className="text-gray-900 font-mono text-xs">{user.id}</dd></div>
                <div className="flex justify-between py-3"><dt className="text-gray-500 text-sm">邮箱</dt><dd className="text-gray-900 text-sm">{user.email}</dd></div>
                <div className="flex justify-between py-3"><dt className="text-gray-500 text-sm">角色</dt><dd className="text-sm font-medium">{user.role === 'admin' ? '管理员' : user.role === 'designer' ? '场景设计者' : '参与者'}</dd></div>
                <div className="flex justify-between py-3">
                  <dt className="text-gray-500 text-sm">联系方式</dt>
                  <dd className="text-gray-900 text-sm">{user.contact_info || <span className="text-gray-400 italic">未设置</span>}</dd>
                </div>
                <div className="flex justify-between py-3">
                  <dt className="text-gray-500 text-sm">个人标签</dt>
                  <dd className="text-gray-900 text-sm">
                    {user.tags && user.tags.length > 0
                      ? user.tags.map((t: string) => (
                          <span key={t} className="inline-block px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded-full text-xs mr-1 mb-1">{t}</span>
                        ))
                      : <span className="text-gray-400 italic">未设置 — 标签将自动用于所有场景匹配</span>
                    }
                  </dd>
                </div>
                <div className="flex justify-between py-3"><dt className="text-gray-500 text-sm">注册时间</dt><dd className="text-gray-900 text-xs">{user.created_at}</dd></div>
              </dl>
              <button
                onClick={() => {
                  setEditContact(user.contact_info || '');
                  setEditTags(user.tags?.join(', ') || '');
                  setEditingProfile(true);
                }}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
              >
                ✏️ 编辑资料
              </button>
            </div>
          ) : (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-4">编辑个人资料</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">联系方式</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">📞</span>
                    <input
                      type="text"
                      value={editContact}
                      onChange={e => setEditContact(e.target.value)}
                      placeholder="微信号 / 手机号 / QQ号"
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">个人标签</label>
                  <input
                    type="text"
                    value={editTags}
                    onChange={e => setEditTags(e.target.value)}
                    placeholder="python, 游戏, 跑步, 摄影 (逗号分隔)"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                  />
                  <p className="text-xs text-gray-400 mt-1">这些标签将自动应用于你参与的所有场景匹配，无需重复填写</p>
                </div>
                {profileError && (
                  <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm flex items-center gap-2">
                    <span>⚠️</span> {profileError}
                  </div>
                )}
                <div className="flex gap-2">
                  <button
                    onClick={async () => {
                      setSavingProfile(true);
                      setProfileError('');
                      try {
                        const tags = editTags
                          .split(/[,，]/)
                          .map(t => t.trim())
                          .filter(t => t.length > 0);
                        await updateProfile({ contact_info: editContact, tags });
                        await refreshUser();
                        setEditingProfile(false);
                      } catch (e: any) {
                        setProfileError(e.message || '保存失败');
                      }
                      setSavingProfile(false);
                    }}
                    disabled={savingProfile}
                    className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                  >
                    {savingProfile ? '保存中...' : '保存'}
                  </button>
                  <button
                    onClick={() => setEditingProfile(false)}
                    className="px-4 py-2 border border-gray-300 text-gray-600 rounded-lg text-sm hover:bg-gray-50 transition-colors"
                  >
                    取消
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Submissions Tab */}
      {tab === 'submissions' && (
        <div>
          {loading ? (
            <div className="space-y-3">
              {[1,2,3].map(i => <div key={i} className="skeleton h-20 w-full rounded-xl" />)}
            </div>
          ) : submissions.length === 0 ? (
            <div className="bg-white rounded-2xl border border-gray-200 p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">📝</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-700 mb-1">还没有提交记录</h3>
              <p className="text-gray-400 text-sm mb-4">提交匹配表单后，你的记录会出现在这里</p>
              <Link href="/" className="inline-flex px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors">
                去浏览场景 →
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {Object.entries(groupedSubmissions).map(([scenarioId, subs]) => {
                const scenarioName = subs[0]?.scenario_name || '未知场景';
                const statusColor: Record<string, string> = { active: 'bg-green-100 text-green-700', draft: 'bg-yellow-100 text-yellow-700', closed: 'bg-gray-100 text-gray-500' };
                const status = subs[0]?.scenario_status || 'unknown';
                return (
                  <details key={scenarioId} className="bg-white rounded-xl border border-gray-200 overflow-hidden group" open>
                    <summary className="px-5 py-3.5 cursor-pointer hover:bg-gray-50 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-gray-400 group-open:rotate-90 transition-transform">▶</span>
                        <span className="font-medium text-gray-900">{scenarioName}</span>
                        <span className={`px-2 py-0.5 rounded-full text-xs ${statusColor[status] || 'bg-gray-100'}`}>{status}</span>
                        <span className="text-xs text-gray-400">{subs.length} 条提交</span>
                      </div>
                      <Link href={`/scenarios/${scenarioId}`} onClick={e => e.stopPropagation()} className="text-xs text-indigo-600 hover:text-indigo-700 font-medium">
                        查看场景 →
                      </Link>
                    </summary>
                    <div className="border-t border-gray-100 divide-y divide-gray-50">
                      {subs.map(sub => (
                        <div key={sub.id} className="px-5 py-3 hover:bg-gray-50 flex items-center justify-between gap-4">
                          <div className="flex-1 min-w-0">
                            <div className="flex flex-wrap gap-x-4 gap-y-1">
                              {Object.entries(sub.form_data).slice(0, 4).map(([k, v]) => (
                                <span key={k} className="text-xs">
                                  <span className="text-gray-400">{k}: </span>
                                  <span className="text-gray-700">{String(v)}</span>
                                </span>
                              ))}
                            </div>
                            <span className="text-xs text-gray-400 mt-1 block">{sub.created_at}</span>
                          </div>
                          <Link
                            href={`/scenarios/${scenarioId}`}
                            className="px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-lg text-xs font-medium hover:bg-indigo-100 whitespace-nowrap transition-colors"
                          >
                            查看匹配
                          </Link>
                        </div>
                      ))}
                    </div>
                  </details>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Matches Tab — THE KEY TAB */}
      {tab === 'matches' && (
        <div>
          {loading ? (
            <div className="space-y-3">
              {[1,2,3].map(i => <div key={i} className="skeleton h-32 w-full rounded-xl" />)}
            </div>
          ) : matches.length === 0 ? (
            <div className="bg-white rounded-2xl border border-gray-200 p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">🔍</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-700 mb-1">还没有匹配结果</h3>
              <p className="text-gray-400 text-sm mb-4">提交匹配表单后，匹配结果将出现在这里</p>
              <Link href="/" className="inline-flex px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors">
                去浏览场景 →
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {matches
                .sort((a, b) => b.similarity_score - a.similarity_score)
                .map((m, i) => {
                  const scorePercent = Math.round(m.similarity_score * 100);
                  const tier =
                    scorePercent >= 85 ? { color: 'from-emerald-400 to-green-500', bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', label: '极佳匹配' }
                    : scorePercent >= 70 ? { color: 'from-blue-400 to-indigo-500', bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200', label: '高度匹配' }
                    : scorePercent >= 50 ? { color: 'from-amber-400 to-orange-500', bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', label: '良好匹配' }
                    : { color: 'from-gray-300 to-gray-400', bg: 'bg-gray-50', text: 'text-gray-500', border: 'border-gray-200', label: '一般匹配' };

                  const formData = m.matched_form_data || {};
                  const contactKey = Object.keys(formData).find(k => k === 'contact' || k === '联系方式');
                  const contactValue = contactKey ? formData[contactKey] : null;
                  const isContactHidden = typeof contactValue === 'string' && contactValue.includes(CONTACT_HIDDEN_MARKER);
                  const displayName = m.matched_user_name || formData.name || '匿名用户';
                  const otherFields = Object.entries(formData).filter(([k]) => k !== contactKey && k !== 'name');

                  return (
                    <div key={m.id || i} className={`bg-white rounded-2xl border ${tier.border} overflow-hidden card-lift transition-all duration-300`}>
                      {/* Score bar */}
                      <div className="h-1.5 bg-gray-100">
                        <div className={`h-full bg-gradient-to-r ${tier.color} transition-all duration-700`} style={{ width: `${scorePercent}%` }} />
                      </div>

                      <div className="p-5">
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex items-center gap-3">
                            <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${tier.color} flex items-center justify-center text-white font-bold text-lg shadow-sm`}>
                              {displayName.charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <h3 className="font-semibold text-gray-900">{displayName}</h3>
                              <Link href={`/scenarios/${m.scenario_id}`} className="text-xs text-indigo-600 hover:text-indigo-700">
                                {m.scenario_name}
                              </Link>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className={`text-xl font-bold ${tier.text}`}>{scorePercent}%</div>
                            <span className={`text-xs px-2 py-0.5 rounded-full ${tier.bg} ${tier.text}`}>{tier.label}</span>
                          </div>
                        </div>

                        {/* Contact — most important! */}
                        {contactEntry(formData, contactKey, isContactHidden)}

                        {/* Other fields */}
                        <div className="grid grid-cols-2 gap-2 mb-3">
                          {otherFields.slice(0, 6).map(([k, v]) => (
                            <div key={k} className="bg-gray-50 rounded-lg px-3 py-2">
                              <span className="text-xs text-gray-400">{k}</span>
                              <p className="text-sm font-medium text-gray-800 break-words">
                                {Array.isArray(v) ? v.join(', ') : String(v ?? '-')}
                              </p>
                            </div>
                          ))}
                        </div>

                        {/* AI Explanation */}
                        {m.explanation && (
                          <details className="group">
                            <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700 py-1">
                              🤖 AI 匹配分析
                            </summary>
                            <div className="mt-2 text-xs text-gray-600 whitespace-pre-line leading-relaxed bg-gray-50 rounded-lg p-3 border border-gray-100">
                              {m.explanation}
                            </div>
                          </details>
                        )}

                        {/* Actions */}
                        <div className="mt-3 pt-3 border-t border-gray-100 flex gap-2">
                          <Link
                            href={`/scenarios/${m.scenario_id}/results`}
                            className="text-xs text-indigo-600 hover:text-indigo-700 font-medium"
                          >
                            查看场景匹配结果 →
                          </Link>
                        </div>
                      </div>
                    </div>
                  );
                })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Helper for contact entry rendering
function contactEntry(formData: Record<string, any>, contactKey: string | undefined, isContactHidden: boolean) {
  if (!contactKey) return null;
  const contactValue = formData[contactKey];
  return (
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
  );
}

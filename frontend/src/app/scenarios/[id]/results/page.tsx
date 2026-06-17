'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import MatchResultCard from '@/components/MatchResultCard';
import { apiGet } from '@/lib/api';
import { useAuth } from '@/lib/auth';

interface Submission {
  id: string;
  scenario_id: string;
  user_id: string;
  form_data: Record<string, any>;
  created_at: string;
}

interface MatchResult {
  submission_id: string;
  matches: any[];
}

interface ScenarioStats {
  scenario_id: string;
  scenario_name: string;
  submission_count: number;
  match_count: number;
  status: string;
  users_with_matches?: number;
  avg_matches_per_user?: number;
}

export default function ResultsPage() {
  const params = useParams();
  const router = useRouter();
  const { user, isAdmin } = useAuth();
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [scenario, setScenario] = useState<any>(null);
  const [stats, setStats] = useState<ScenarioStats | null>(null);
  const [detailedStats, setDetailedStats] = useState<any>(null);
  const [selectedSub, setSelectedSub] = useState<string>('');
  const [matchResult, setMatchResult] = useState<MatchResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [matchLoading, setMatchLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, [params.id]);

  const fetchData = async () => {
    // Fetch scenario first (public, no auth needed)
    try {
      const scenarioData = await apiGet(`/scenarios/${params.id}`);
      setScenario(scenarioData);
    } catch (err) {
      console.error('Failed to fetch scenario:', err);
      setLoading(false);
      return;
    }

    // Fetch submissions and stats independently (require auth, may fail for non-participants)
    try {
      const subs = await apiGet(`/submissions/scenario/${params.id}`);
      setSubmissions(subs);
      if (subs.length > 0) setSelectedSub(subs[0].id);
    } catch (err) {
      console.error('Failed to fetch submissions:', err);
      setSubmissions([]);
    }

    try {
      const statsData = await apiGet(`/scenarios/${params.id}/stats`);
      setStats(statsData);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }

    try {
      const detailedStatsData = await apiGet(`/matching/stats/scenario/${params.id}`);
      setDetailedStats(detailedStatsData);
    } catch (err) {
      console.error('Failed to fetch matching stats:', err);
    }

    setLoading(false);
  };

  useEffect(() => {
    if (selectedSub) {
      fetchMatchResults(selectedSub);
    }
  }, [selectedSub]);

  const fetchMatchResults = async (subId: string) => {
    setMatchLoading(true);
    try {
      const data = await apiGet(`/matching/results/${subId}`);
      setMatchResult(data);
    } catch (err) {
      console.error('Failed to fetch match results:', err);
    }
    setMatchLoading(false);
  };

  const selectedSubmission = submissions.find(s => s.id === selectedSub);
  const selectedName = selectedSubmission?.form_data?.name || '匿名用户';

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-2xl border border-gray-200 p-8">
          <div className="skeleton h-8 w-48 mb-4" />
          <div className="grid grid-cols-3 gap-4 mb-8">
            <div className="skeleton h-24 w-full" />
            <div className="skeleton h-24 w-full" />
            <div className="skeleton h-24 w-full" />
          </div>
          <div className="skeleton h-64 w-full" />
        </div>
      </div>
    );
  }

  if (!scenario) {
    return (
      <div className="max-w-xl mx-auto text-center py-16">
        <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <span className="text-4xl">😕</span>
        </div>
        <h2 className="text-xl font-semibold text-gray-700 mb-2">场景不存在</h2>
        <button onClick={() => router.push('/')} className="mt-4 px-6 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors">
          ← 返回场景广场
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto animate-fade-in">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-400 mb-6">
        <Link href="/" className="hover:text-gray-600 transition-colors">场景广场</Link>
        <span>/</span>
        <Link href={`/scenarios/${params.id}`} className="hover:text-gray-600 transition-colors truncate">{scenario.name}</Link>
        <span>/</span>
        <span className="text-gray-700 font-medium">匹配结果</span>
        {isAdmin && <span className="ml-2 px-2 py-0.5 bg-red-100 text-red-600 rounded text-xs font-medium">管理员视图</span>}
      </div>

      {/* Header */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-6 shadow-sm">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-1">{scenario.name}</h1>
            <p className="text-gray-500 text-sm">匹配结果总览</p>
          </div>
          <div className="flex gap-2">
            <Link
              href={`/scenarios/${params.id}`}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
            >
              我要参与
            </Link>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center card-lift">
          <div className="text-3xl font-bold text-indigo-600">{stats?.submission_count || 0}</div>
          <div className="text-xs text-gray-500 mt-1">总参与者</div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center card-lift">
          <div className="text-3xl font-bold text-green-600">{stats?.match_count || 0}</div>
          <div className="text-xs text-gray-500 mt-1">总匹配对数</div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center card-lift">
          <div className="text-3xl font-bold text-blue-600">{detailedStats?.users_with_matches || 0}</div>
          <div className="text-xs text-gray-500 mt-1">已匹配人数</div>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 p-4 text-center card-lift">
          <div className="text-3xl font-bold text-amber-600">
            {detailedStats?.avg_matches_per_user?.toFixed(1) || '0'}
          </div>
          <div className="text-xs text-gray-500 mt-1">平均匹配/人</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left: Participant List */}
        <div className="md:col-span-1">
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden sticky top-20">
            <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
              <h2 className="text-sm font-semibold text-gray-700">参与者列表</h2>
            </div>
            {submissions.length === 0 ? (
              <div className="p-6 text-center">
                <div className="text-3xl mb-2">📭</div>
                <p className="text-sm text-gray-500">暂无参与者</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-50 max-h-[500px] overflow-y-auto">
                {submissions.map((sub, i) => {
                  const name = sub.form_data?.name || '匿名用户';
                  const contact = sub.form_data?.contact || sub.form_data?.联系方式 || '';
                  const isSelected = selectedSub === sub.id;
                  return (
                    <button
                      key={sub.id}
                      onClick={() => setSelectedSub(sub.id)}
                      className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors ${
                        isSelected ? 'bg-indigo-50 border-l-2 border-l-indigo-600' : ''
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold ${
                          isSelected ? 'bg-indigo-600' : 'bg-gray-400'
                        }`}>
                          {name.charAt(0).toUpperCase()}
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">{name}</p>
                          <p className="text-xs text-gray-400 truncate">
                            {contact ? String(contact).slice(0, 20) : new Date(sub.created_at).toLocaleDateString('zh-CN')}
                          </p>
                        </div>
                        {isSelected && <span className="ml-auto text-indigo-600 text-xs">查看中</span>}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right: Match Results */}
        <div className="md:col-span-2">
          {selectedSub && (
            <div>
              {/* Selected participant info */}
              <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl border border-indigo-100 p-4 mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center text-white font-bold text-lg">
                    {selectedName.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">{selectedName} 的匹配结果</p>
                    <p className="text-xs text-gray-500">
                      {selectedSubmission?.created_at ? new Date(selectedSubmission.created_at).toLocaleDateString('zh-CN') : ''}
                    </p>
                  </div>
                </div>
              </div>

              {matchLoading ? (
                <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
                  <div className="animate-spin inline-block w-8 h-8 border-4 border-indigo-200 border-t-indigo-600 rounded-full mb-3"></div>
                  <p className="text-sm text-gray-500">加载匹配结果...</p>
                </div>
              ) : matchResult && matchResult.matches && matchResult.matches.length > 0 ? (
                <div className="space-y-4">
                  {matchResult.matches
                    .sort((a: any, b: any) => b.similarity_score - a.similarity_score)
                    .map((match: any, i: number) => (
                      <MatchResultCard
                        key={match.matched_submission_id}
                        match={match}
                        rank={i + 1}
                      />
                    ))}
                </div>
              ) : (
                <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
                  <div className="text-4xl mb-3">🔍</div>
                  <p className="text-gray-600 font-medium mb-1">暂未触发匹配</p>
                  <p className="text-gray-400 text-sm">该参与者尚未运行匹配算法</p>
                </div>
              )}
            </div>
          )}

          {/* No selection */}
          {!selectedSub && submissions.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
              <div className="text-4xl mb-3">👈</div>
              <p className="text-gray-500 text-sm">请从左侧列表选择一位参与者查看匹配结果</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

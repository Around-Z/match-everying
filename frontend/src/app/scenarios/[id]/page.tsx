'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import DynamicFormRenderer from '@/components/DynamicFormRenderer';
import MatchResultCard from '@/components/MatchResultCard';
import { apiGet, apiPost } from '@/lib/api';
import { useAuth } from '@/lib/auth';

interface Scenario {
  id: string;
  name: string;
  description: string;
  status: string;
  form_schema: { fields: any[] };
  match_config: any;
  ui_config: any;
  submission_count: number;
}

export default function ScenarioPage() {
  const params = useParams();
  const router = useRouter();
  const { user, isAuthenticated } = useAuth();
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [matchResult, setMatchResult] = useState<any>(null);
  const [matching, setMatching] = useState(false);
  const [error, setError] = useState('');

  // Existing submission state
  const [existingSubmission, setExistingSubmission] = useState<any>(null);
  const [existingMatches, setExistingMatches] = useState<any[]>([]);
  const [loadingExisting, setLoadingExisting] = useState(false);

  useEffect(() => {
    fetchScenario();
  }, [params.id]);

  const fetchScenario = async () => {
    try {
      const data = await apiGet(`/scenarios/${params.id}`);
      setScenario(data);
      // Check if user already submitted to this scenario
      await checkExistingSubmission();
    } catch (err) {
      setError('场景不存在或已关闭');
      setLoading(false);
    }
  };

  const checkExistingSubmission = async () => {
    if (!isAuthenticated) { setLoading(false); return; }
    setLoadingExisting(true);
    try {
      const subs = await apiGet(`/submissions/scenario/${params.id}`);
      if (subs && subs.length > 0) {
        const sub = subs[0];
        setExistingSubmission(sub);
        // Fetch existing match results
        try {
          const matchData = await apiGet(`/matching/results/${sub.id}`);
          if (matchData && matchData.matches) {
            setExistingMatches(matchData.matches);
          }
        } catch (matchErr) {
          console.error('Failed to fetch existing matches:', matchErr);
        }
      }
    } catch (subErr) {
      // Not submitted or not authenticated — that's fine
    }
    setLoadingExisting(false);
    setLoading(false);
  };

  const handleSubmit = async (formData: Record<string, any>) => {
    setSubmitting(true);
    setError('');
    try {
      const submission = await apiPost('/submissions', {
        scenario_id: params.id,
        form_data: formData,
      });
      setExistingSubmission(submission);
      setSubmitSuccess(true);

      // Auto-run matching
      setMatching(true);
      try {
        const matchData = await apiPost(`/matching/run/${submission.id}`);
        setMatchResult(matchData);
      } catch (matchErr) {
        console.error('Matching failed:', matchErr);
      }
      setMatching(false);
    } catch (err: any) {
      setError(err.message || '提交失败，请重试');
    }
    setSubmitting(false);
  };

  if (loading) {
    return (
      <div className="max-w-xl mx-auto">
        <div className="bg-white rounded-2xl border border-gray-200 p-8">
          <div className="skeleton h-8 w-48 mb-4" />
          <div className="skeleton h-4 w-64 mb-2" />
          <div className="skeleton h-4 w-56 mb-8" />
          <div className="space-y-4">
            <div className="skeleton h-12 w-full" />
            <div className="skeleton h-12 w-full" />
            <div className="skeleton h-24 w-full" />
          </div>
        </div>
      </div>
    );
  }

  if (error && !scenario) {
    return (
      <div className="max-w-xl mx-auto text-center py-16">
        <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <span className="text-4xl">😕</span>
        </div>
        <h2 className="text-xl font-semibold text-gray-700 mb-2">{error}</h2>
        <button
          onClick={() => router.push('/')}
          className="mt-4 px-6 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors"
        >
          ← 返回场景广场
        </button>
      </div>
    );
  }

  if (!scenario) return null;

  // ===== RENDER: Existing submission — show match results =====
  const showExistingResults = existingSubmission && !submitSuccess;

  if (showExistingResults) {
    const matches = existingMatches.length > 0
      ? existingMatches.sort((a: any, b: any) => b.similarity_score - a.similarity_score)
      : [];
    const topMatch = matches.length > 0 ? matches[0] : null;

    return (
      <div className="max-w-3xl mx-auto animate-fade-in">
        {/* Header */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-6 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <Link href="/" className="hover:text-gray-600 transition-colors">场景广场</Link>
              <span>/</span>
              <span className="text-gray-700 font-medium">{scenario.name}</span>
            </div>
            <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
              scenario.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
            }`}>
              {scenario.status === 'active' ? '进行中' : scenario.status}
            </span>
          </div>

          {/* Already submitted banner */}
          <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4 mt-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-2xl">✅</span>
              <div>
                <p className="text-sm font-medium text-indigo-800">你已提交过此场景</p>
                <p className="text-xs text-indigo-600">
                  {matches.length > 0 ? `找到 ${matches.length} 位匹配对象` : '等待匹配中...'}
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                setExistingSubmission(null);
                setExistingMatches([]);
                setSubmitSuccess(false);
                setMatchResult(null);
              }}
              className="px-3 py-1.5 text-xs font-medium text-indigo-700 bg-white border border-indigo-200 rounded-lg hover:bg-indigo-100 transition-colors"
            >
              修改提交
            </button>
          </div>
        </div>

        {/* Match Results */}
        {matches.length > 0 ? (
          <div>
            <h2 className="text-lg font-bold text-gray-900 mb-4">🎯 你的匹配结果</h2>
            <div className="space-y-4">
              {matches.map((match: any, i: number) => (
                <MatchResultCard
                  key={match.matched_submission_id}
                  match={match}
                  rank={i + 1}
                />
              ))}
            </div>
            <div className="text-center mt-6">
              <Link
                href={`/scenarios/${params.id}/results`}
                className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
              >
                查看全部参与者 →
              </Link>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-gray-200 p-8 text-center">
            <div className="text-5xl mb-4">🔍</div>
            <h3 className="text-lg font-semibold text-gray-700 mb-2">暂未找到匹配</h3>
            <p className="text-gray-500 text-sm">
              当有更多参与者提交后，AI 将自动为你寻找匹配对象。
            </p>
          </div>
        )}
      </div>
    );
  }

  // ===== SUCCESS STATE — Just submitted, showing results =====
  if (submitSuccess) {
    const matches = matchResult?.matches || [];

    return (
      <div className="max-w-3xl mx-auto animate-fade-in">
        {/* Success Hero */}
        <div className="bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-2xl p-8 mb-8 text-white text-center shadow-lg">
          <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-4 text-3xl backdrop-blur">
            🎉
          </div>
          <h1 className="text-2xl font-bold mb-2">提交成功！</h1>
          <p className="text-white/80 text-sm">
            {matching ? 'AI 正在为你分析最佳匹配...'
              : matches.length > 0 ? `为你找到 ${matches.length} 位匹配对象`
              : '当有更多参与者时，匹配结果将自动生成'}
          </p>
        </div>

        {/* Matching in progress */}
        {matching && (
          <div className="bg-white rounded-2xl border border-gray-200 p-8 text-center mb-8">
            <div className="w-16 h-16 mx-auto mb-4 relative">
              <div className="absolute inset-0 bg-indigo-100 rounded-full animate-ping opacity-75"></div>
              <div className="relative w-16 h-16 bg-indigo-600 rounded-full flex items-center justify-center">
                <svg className="animate-spin h-8 w-8 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                </svg>
              </div>
            </div>
            <p className="text-gray-600 font-medium">AI 正在分析匹配...</p>
            <p className="text-gray-400 text-sm mt-1">正在计算语义相似度，寻找最适合你的人</p>
          </div>
        )}

        {/* Match Results */}
        {!matching && matches.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900">🎯 匹配结果</h2>
              <Link href={`/scenarios/${params.id}/results`} className="text-sm text-indigo-600 hover:text-indigo-700 font-medium">
                查看全部参与者 →
              </Link>
            </div>
            <div className="space-y-4">
              {matches.map((match: any, i: number) => (
                <MatchResultCard key={match.matched_submission_id} match={match} rank={i + 1} />
              ))}
            </div>
          </div>
        )}

        {/* No matches */}
        {!matching && matches.length === 0 && (
          <div className="bg-white rounded-2xl border border-gray-200 p-8 text-center">
            <div className="text-5xl mb-4">🔍</div>
            <h3 className="text-lg font-semibold text-gray-700 mb-2">暂未找到匹配</h3>
            <p className="text-gray-500 text-sm mb-4">当有更多参与者提交后，AI 将自动为你寻找匹配对象。</p>
            <div className="text-xs text-gray-400 bg-gray-50 rounded-lg p-3 inline-block">
              当前场景已有 {scenario.submission_count} 人参与
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 justify-center mt-8">
          <button
            onClick={() => {
              setSubmitSuccess(false);
              setMatchResult(null);
              setExistingSubmission(null);
              setExistingMatches([]);
            }}
            className="px-6 py-2.5 bg-white border border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors"
          >
            修改提交
          </button>
          <Link href="/me" className="px-6 py-2.5 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition-colors">
            查看我的匹配 →
          </Link>
        </div>
      </div>
    );
  }

  // ===== FORM STATE — Not yet submitted =====
  return (
    <div className="max-w-xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-400 mb-6">
        <Link href="/" className="hover:text-gray-600 transition-colors">场景广场</Link>
        <span>/</span>
        <span className="text-gray-700 font-medium truncate">{scenario.name}</span>
      </div>

      {/* Scenario Header */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-6 shadow-sm">
        <div className="flex items-start justify-between mb-3">
          <h1 className="text-xl font-bold text-gray-900">{scenario.name}</h1>
          <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
            scenario.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
          }`}>
            {scenario.status === 'active' ? '进行中' : scenario.status}
          </span>
        </div>
        <p className="text-sm text-gray-600 mb-4">{scenario.description}</p>

        {/* Required fields */}
        <div className="flex flex-wrap gap-2">
          {scenario.form_schema.fields.filter((f: any) => f.required).map((f: any) => (
            <span key={f.key} className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${
              f.type === 'contact' ? 'bg-green-100 text-green-700 border border-green-200' : 'bg-gray-100 text-gray-600'
            }`}>
              {f.type === 'contact' ? '📞' : '•'} {f.label} (必填)
            </span>
          ))}
        </div>

        {!isAuthenticated && (
          <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-700 flex items-center gap-2">
            <span>⚠️</span>
            <span>建议先<Link href="/login" className="text-amber-800 font-medium underline">登录</Link>再提交，方便追踪你的匹配记录</span>
          </div>
        )}
      </div>

      {/* Form */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
        <DynamicFormRenderer
          formSchema={scenario.form_schema}
          onSubmit={handleSubmit}
          submitLabel="提交并查看匹配"
          submitting={submitting}
          initialValues={user?.contact_info ? { contact: user.contact_info } : undefined}
        />
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm">{error}</div>
      )}

      <div className="text-center mt-6 pb-8">
        <Link href="/" className="text-sm text-gray-400 hover:text-gray-600 transition-colors">
          ← 返回场景广场
        </Link>
      </div>
    </div>
  );
}

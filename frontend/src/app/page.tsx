'use client';

import { useState, useEffect } from 'react';
import ScenarioCard from '@/components/ScenarioCard';
import CreateScenarioModal from '@/components/CreateScenarioModal';
import { apiGet } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import Link from 'next/link';

interface Scenario {
  id: string;
  creator_id: string;
  name: string;
  description: string;
  status: string;
  created_at: string;
  submission_count: number;
  form_schema: { fields: any[] };
  match_config: any;
  ui_config: any;
}

export default function HomePage() {
  const { isAuthenticated } = useAuth();
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [filter, setFilter] = useState<string>('');
  const [stats, setStats] = useState<any>(null);

  const fetchScenarios = async () => {
    setLoading(true);
    setLoadError('');
    try {
      const path = filter ? `/scenarios?status=${filter}` : '/scenarios';
      const data = await apiGet(path);
      setScenarios(data);
    } catch (err: any) {
      console.error('Failed to fetch scenarios:', err);
      setLoadError(err.message || '加载场景失败');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchScenarios();
  }, [filter]);

  // Fetch stats for banner
  useEffect(() => {
    apiGet('/admin/stats').then(setStats).catch(() => {});
  }, []);

  const activeScenarios = scenarios.filter(s => s.status === 'active');
  const draftScenarios = scenarios.filter(s => s.status === 'draft');
  const closedScenarios = scenarios.filter(s => s.status === 'closed');

  return (
    <div className="animate-fade-in">
      {/* Hero Section */}
      <div className="relative mb-12 overflow-hidden">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-50 via-white to-purple-50 rounded-3xl -mx-4" />

        <div className="relative text-center py-12 px-4">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-indigo-50 rounded-full text-sm text-indigo-700 mb-6">
            <span className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse"></span>
            AI 驱动的智能匹配平台
          </div>

          <h1 className="text-4xl md:text-5xl font-extrabold text-gray-900 mb-4 tracking-tight">
            找到与你
            <span className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent"> 最契合 </span>
            的那个人
          </h1>

          <p className="text-base md:text-lg text-gray-500 mb-8 max-w-xl mx-auto leading-relaxed">
            基于 AI 语义理解，深入分析你的需求与特质，精准匹配最合适的人选。
            无论找队友、找搭档还是找伙伴，都能在这里找到。
          </p>

          <div className="flex gap-3 justify-center flex-wrap">
            <button
              onClick={() => setShowCreate(true)}
              className="px-6 py-3 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-200 hover:shadow-xl hover:shadow-indigo-200 hover:-translate-y-0.5"
            >
              ✨ 创建匹配场景
            </button>
            {!isAuthenticated && (
              <Link
                href="/register"
                className="px-6 py-3 bg-white text-gray-700 rounded-xl font-medium border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-all shadow-sm"
              >
                免费注册
              </Link>
            )}
            {isAuthenticated && (
              <Link
                href="/me"
                className="px-6 py-3 bg-white text-gray-700 rounded-xl font-medium border border-gray-200 hover:border-gray-300 hover:bg-gray-50 transition-all shadow-sm"
              >
                我的匹配 →
              </Link>
            )}
          </div>

          {/* Stats banner */}
          {stats && (
            <div className="flex justify-center gap-8 mt-10 text-sm">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">{stats.total_scenarios || 0}</div>
                <div className="text-gray-400">匹配场景</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">{stats.total_users || 0}</div>
                <div className="text-gray-400">注册用户</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">{stats.total_matches || 0}</div>
                <div className="text-gray-400">匹配对数</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex gap-2">
          {[
            { key: '', label: '全部场景', icon: '📋' },
            { key: 'active', label: '进行中', icon: '🟢' },
            { key: 'draft', label: '草稿', icon: '📝' },
            { key: 'closed', label: '已关闭', icon: '🔒' },
          ].map(f => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                filter === f.key
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
              }`}
            >
              {f.icon} {f.label}
            </button>
          ))}
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="px-4 py-2 border border-indigo-200 text-indigo-700 rounded-xl text-sm font-medium hover:bg-indigo-50 transition-colors"
        >
          + 新建场景
        </button>
      </div>

      {/* Loading */}
      {loading && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="bg-white rounded-2xl border border-gray-200 p-5">
              <div className="skeleton h-6 w-32 mb-3" />
              <div className="skeleton h-4 w-full mb-2" />
              <div className="skeleton h-4 w-3/4 mb-4" />
              <div className="flex gap-2">
                <div className="skeleton h-8 w-20 rounded-full" />
                <div className="skeleton h-8 w-20 rounded-full" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Active Scenarios */}
      {!loading && activeScenarios.length > 0 && (
        <section className="mb-10">
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-lg font-bold text-gray-900">进行中的场景</h2>
            <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-medium">{activeScenarios.length}</span>
          </div>
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {activeScenarios.map(s => (
              <ScenarioCard key={s.id} scenario={s} onRefresh={fetchScenarios} />
            ))}
          </div>
        </section>
      )}

      {/* Draft Scenarios */}
      {!loading && draftScenarios.length > 0 && (
        <section className="mb-10">
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-lg font-bold text-gray-900">草稿</h2>
            <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded-full text-xs font-medium">{draftScenarios.length}</span>
          </div>
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {draftScenarios.map(s => (
              <ScenarioCard key={s.id} scenario={s} onRefresh={fetchScenarios} />
            ))}
          </div>
        </section>
      )}

      {/* Closed Scenarios */}
      {!loading && closedScenarios.length > 0 && (
        <section className="mb-10">
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-lg font-bold text-gray-900">已关闭</h2>
            <span className="px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full text-xs font-medium">{closedScenarios.length}</span>
          </div>
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3 opacity-60">
            {closedScenarios.map(s => (
              <ScenarioCard key={s.id} scenario={s} onRefresh={fetchScenarios} />
            ))}
          </div>
        </section>
      )}

      {/* Load error */}
      {!loading && loadError && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-8 text-center mb-8">
          <div className="text-4xl mb-3">⚠️</div>
          <p className="text-amber-800 font-medium mb-2">加载失败</p>
          <p className="text-amber-600 text-sm mb-4">{loadError}</p>
          <button onClick={fetchScenarios} className="px-4 py-2 bg-amber-600 text-white rounded-lg text-sm hover:bg-amber-700">
            重新加载
          </button>
        </div>
      )}

      {/* Empty state */}
      {!loading && !loadError && scenarios.length === 0 && (
        <div className="bg-white rounded-3xl border border-gray-200 p-16 text-center">
          <div className="w-20 h-20 bg-indigo-50 rounded-full flex items-center justify-center mx-auto mb-6">
            <span className="text-4xl">📋</span>
          </div>
          <h3 className="text-xl font-bold text-gray-800 mb-2">还没有匹配场景</h3>
          <p className="text-gray-500 mb-6 max-w-md mx-auto">
            创建你的第一个匹配场景，填写匹配条件，开始发现与你最契合的人。
          </p>
          <button
            onClick={() => setShowCreate(true)}
            className="px-6 py-3 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-200"
          >
            ✨ 创建第一个场景
          </button>
        </div>
      )}

      {/* Create Modal */}
      {showCreate && (
        <CreateScenarioModal
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false);
            fetchScenarios();
          }}
        />
      )}
    </div>
  );
}

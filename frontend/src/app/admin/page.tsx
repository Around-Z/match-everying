'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth';
import { apiGet, apiPut } from '@/lib/api';

interface Stats {
  total_scenarios: number;
  active_scenarios: number;
  total_users: number;
  users_by_role: Record<string, number>;
  total_submissions: number;
  total_matches: number;
  recent_users_7d: number;
  recent_submissions_7d: number;
}

interface UserItem {
  id: string;
  email: string;
  username: string;
  role: string;
  created_at: string;
}

export default function AdminPage() {
  const { user, isAdmin, loading: authLoading } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<Stats | null>(null);
  const [users, setUsers] = useState<UserItem[]>([]);
  const [tab, setTab] = useState<'dashboard' | 'users'>('dashboard');

  useEffect(() => {
    if (!authLoading && !isAdmin) router.push('/');
  }, [authLoading, isAdmin]);

  useEffect(() => {
    if (!isAdmin) return;
    fetchStats();
    if (tab === 'users') fetchUsers();
  }, [isAdmin, tab]);

  const fetchStats = async () => {
    try { setStats(await apiGet('/admin/stats')); } catch (e) { console.error(e); }
  };

  const fetchUsers = async () => {
    try {
      const data = await apiGet('/admin/users');
      setUsers(data.users || []);
    } catch (e) { console.error(e); }
  };

  const updateUserRole = async (userId: string, newRole: string) => {
    try {
      await apiPut(`/admin/users/${userId}/role`, { role: newRole });
      fetchUsers();
    } catch (e) { console.error(e); }
  };

  if (authLoading || !isAdmin) {
    return (
      <div className="text-center py-16">
        <div className="w-12 h-12 mx-auto mb-4 relative">
          <div className="absolute inset-0 bg-indigo-100 rounded-full animate-ping opacity-75"></div>
          <div className="relative w-12 h-12 bg-indigo-600 rounded-full flex items-center justify-center">
            <svg className="animate-spin h-6 w-6 text-white" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
            </svg>
          </div>
        </div>
        <p className="text-gray-500">验证管理员权限...</p>
      </div>
    );
  }

  const statCards = stats ? [
    { label: '场景总数', value: stats.total_scenarios, sub: `${stats.active_scenarios} 进行中`, icon: '📋', gradient: 'from-indigo-500 to-blue-500' },
    { label: '用户总数', value: stats.total_users, sub: `参与${stats.users_by_role?.participant||0} · 设计${stats.users_by_role?.designer||0}`, icon: '👥', gradient: 'from-emerald-500 to-teal-500' },
    { label: '提交总数', value: stats.total_submissions, sub: `近7天 +${stats.recent_submissions_7d}`, icon: '📝', gradient: 'from-cyan-500 to-blue-500' },
    { label: '匹配对数', value: stats.total_matches, sub: `近7天 +${stats.recent_users_7d} 新用户`, icon: '🔗', gradient: 'from-purple-500 to-pink-500' },
  ] : [];

  return (
    <div className="max-w-6xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-red-100 rounded-xl flex items-center justify-center text-xl">⚙️</div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">管理后台</h1>
              <p className="text-sm text-gray-500">系统管理与数据监控</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="px-2.5 py-1 bg-red-100 text-red-700 rounded-full text-xs font-medium">管理员视图</span>
            <Link href="/" className="text-sm text-gray-400 hover:text-gray-600 transition-colors">← 返回首页</Link>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-xl p-1.5 mb-6 w-fit">
        <button onClick={() => setTab('dashboard')} className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${tab === 'dashboard' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>
          📊 仪表盘
        </button>
        <button onClick={() => setTab('users')} className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${tab === 'users' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>
          👥 用户管理
        </button>
      </div>

      {/* Dashboard */}
      {tab === 'dashboard' && (
        <div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {statCards.map(card => (
              <div key={card.label} className="bg-white rounded-xl border border-gray-200 p-5 card-lift relative overflow-hidden">
                <div className={`absolute top-0 right-0 w-16 h-16 bg-gradient-to-bl ${card.gradient} opacity-10 rounded-bl-3xl`}></div>
                <div className="relative">
                  <span className="text-2xl">{card.icon}</span>
                  <p className="text-3xl font-bold text-gray-900 mt-2">{card.value}</p>
                  <p className="text-sm text-gray-500 mt-0.5">{card.label}</p>
                  <p className="text-xs text-gray-400 mt-1">{card.sub}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Users */}
      {tab === 'users' && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
          <div className="px-5 py-3 border-b border-gray-100 bg-gray-50 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-700">用户列表 ({users.length})</h3>
            <button onClick={fetchUsers} className="text-xs text-indigo-600 hover:text-indigo-700 font-medium">刷新</button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left px-5 py-3 font-medium text-gray-500 text-xs">用户名</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500 text-xs">邮箱</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500 text-xs">角色</th>
                  <th className="text-left px-5 py-3 font-medium text-gray-500 text-xs">注册时间</th>
                  <th className="text-right px-5 py-3 font-medium text-gray-500 text-xs">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {users.map(u => (
                  <tr key={u.id} className="hover:bg-gray-50/50 transition-colors">
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2.5">
                        <div className={`w-7 h-7 rounded-lg flex items-center justify-center text-white text-xs font-bold ${
                          u.role === 'admin' ? 'bg-red-500' : u.role === 'designer' ? 'bg-indigo-500' : 'bg-green-500'
                        }`}>
                          {u.username.charAt(0).toUpperCase()}
                        </div>
                        <span className="font-medium text-gray-900">{u.username}</span>
                      </div>
                    </td>
                    <td className="px-5 py-3 text-gray-500 font-mono text-xs">{u.email}</td>
                    <td className="px-5 py-3">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        u.role === 'admin' ? 'bg-red-50 text-red-700 border border-red-200'
                        : u.role === 'designer' ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                        : 'bg-green-50 text-green-700 border border-green-200'
                      }`}>
                        {u.role === 'admin' ? '管理员' : u.role === 'designer' ? '设计者' : '参与者'}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-gray-400 text-xs">{u.created_at}</td>
                    <td className="px-5 py-3 text-right">
                      <select
                        value={u.role}
                        onChange={e => updateUserRole(u.id, e.target.value)}
                        className="text-xs border border-gray-200 rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none bg-gray-50 cursor-pointer"
                      >
                        <option value="participant">参与者</option>
                        <option value="designer">设计者</option>
                        <option value="admin">管理员</option>
                      </select>
                    </td>
                  </tr>
                ))}
                {users.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-5 py-12 text-center text-gray-400">暂无用户数据</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

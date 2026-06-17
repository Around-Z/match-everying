'use client';

import Link from 'next/link';
import { apiPut, apiDelete } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { useState } from 'react';

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

interface Props {
  scenario: Scenario;
  onRefresh: () => void;
}

const TOPIC_ICONS: Record<string, string> = {
  game: '🎮', gaming: '🎮', 游戏: '🎮', 王者荣耀: '👑', lol: '⚔️',
  study: '📚', 学习: '📚', 教育: '📖', course: '🎓',
  work: '💼', 工作: '💼', 项目: '🚀', project: '🚀', team: '👥',
  friend: '🤝', 交友: '💕', 社交: '💬', social: '💬',
  sport: '⚽', 运动: '🏃', fitness: '💪', 健身: '💪',
  travel: '✈️', 旅行: '🌍',
  music: '🎵', 音乐: '🎶',
  food: '🍔', 美食: '🍜',
};

function guessIcon(name: string, description: string): string {
  const text = (name + description).toLowerCase();
  for (const [key, icon] of Object.entries(TOPIC_ICONS)) {
    if (text.includes(key)) return icon;
  }
  return '🎯';
}

export default function ScenarioCard({ scenario, onRefresh }: Props) {
  const { user, isAdmin } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  const isOwner = user?.id === scenario.creator_id;
  const canManage = isAdmin || isOwner;

  const statusConfig: Record<string, { bg: string; text: string; border: string; label: string }> = {
    active: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200', label: '进行中' },
    draft: { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200', label: '草稿' },
    closed: { bg: 'bg-gray-50', text: 'text-gray-500', border: 'border-gray-200', label: '已关闭' },
  };

  const sc = statusConfig[scenario.status] || statusConfig.closed;
  const fieldCount = scenario.form_schema?.fields?.length || 0;
  const hasContact = scenario.form_schema?.fields?.some((f: any) => f.type === 'contact');
  const icon = guessIcon(scenario.name, scenario.description);

  const handlePublish = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    await apiPut(`/scenarios/${scenario.id}`, { status: 'active' });
    onRefresh();
  };

  const handleClose = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm('确定关闭这个场景吗？')) return;
    await apiPut(`/scenarios/${scenario.id}`, { status: 'closed' });
    onRefresh();
  };

  const handleDelete = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm('确定删除这个场景吗？所有提交数据也会被删除。')) return;
    await apiDelete(`/scenarios/${scenario.id}`);
    onRefresh();
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden card-lift group">
      {/* Top accent bar */}
      <div className={`h-1 ${
        scenario.status === 'active' ? 'bg-gradient-to-r from-green-400 to-emerald-500'
        : scenario.status === 'draft' ? 'bg-gradient-to-r from-yellow-400 to-amber-500'
        : 'bg-gradient-to-r from-gray-300 to-gray-400'
      }`} />

      <div className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <span className="text-2xl flex-shrink-0">{icon}</span>
            <div className="min-w-0">
              <h3 className="font-semibold text-gray-900 truncate">{scenario.name}</h3>
              <p className="text-xs text-gray-400">
                {new Date(scenario.created_at).toLocaleDateString('zh-CN')}
              </p>
            </div>
          </div>
          <span className={`flex-shrink-0 px-2.5 py-0.5 rounded-full text-xs border ${sc.bg} ${sc.text} ${sc.border}`}>
            {sc.label}
          </span>
        </div>

        {/* Description */}
        <p className="text-sm text-gray-500 mb-4 line-clamp-2 leading-relaxed">
          {scenario.description || '暂无描述'}
        </p>

        {/* Meta chips */}
        <div className="flex flex-wrap gap-2 mb-4">
          <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-gray-100 rounded-full text-xs text-gray-600">
            📝 {fieldCount} 字段
          </span>
          <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-gray-100 rounded-full text-xs text-gray-600">
            👥 {scenario.submission_count} 人参与
          </span>
          {hasContact && (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-green-50 rounded-full text-xs text-green-700 border border-green-100">
              📞 含联系方式
            </span>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex gap-2 items-center">
          {scenario.status === 'active' && (
            <Link
              href={`/scenarios/${scenario.id}`}
              className="flex-1 text-center px-4 py-2.5 bg-indigo-600 text-white rounded-xl text-sm font-medium hover:bg-indigo-700 transition-all shadow-sm hover:shadow-md"
            >
              立即参与
            </Link>
          )}
          {scenario.status === 'draft' && canManage && (
            <button
              onClick={handlePublish}
              className="flex-1 px-4 py-2.5 bg-green-600 text-white rounded-xl text-sm font-medium hover:bg-green-700 transition-all shadow-sm hover:shadow-md"
            >
              发布场景
            </button>
          )}
          {scenario.status === 'active' && (
            <Link
              href={`/scenarios/${scenario.id}/results`}
              className="px-4 py-2.5 border border-gray-200 text-gray-600 rounded-xl text-sm hover:bg-gray-50 hover:border-gray-300 transition-all"
            >
              查看结果
            </Link>
          )}

          {/* More menu — only for owners and admins */}
          {canManage && (
            <div className="relative">
              <button
                onClick={(e) => { e.preventDefault(); e.stopPropagation(); setMenuOpen(!menuOpen); }}
                className="px-2 py-2.5 border border-gray-200 text-gray-400 rounded-xl text-sm hover:bg-gray-50 hover:text-gray-600 transition-all"
              >
                ⋯
              </button>
              {menuOpen && (
                <>
                  <div className="fixed inset-0 z-10" onClick={(e) => { e.preventDefault(); e.stopPropagation(); setMenuOpen(false); }} />
                  <div className="absolute right-0 bottom-full mb-2 w-32 bg-white rounded-xl border border-gray-200 shadow-lg z-20 py-1">
                    {scenario.status === 'active' && (
                      <button onClick={handleClose} className="w-full text-left px-4 py-2 text-sm text-gray-600 hover:bg-gray-50">
                        关闭场景
                      </button>
                    )}
                    <button onClick={handleDelete} className="w-full text-left px-4 py-2 text-sm text-red-500 hover:bg-red-50">
                      删除场景
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

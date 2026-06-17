'use client';

import { useState } from 'react';
import DynamicFormRenderer from './DynamicFormRenderer';
import { apiPost } from '@/lib/api';

interface Props {
  onClose: () => void;
  onCreated: () => void;
}

export default function CreateScenarioModal({ onClose, onCreated }: Props) {
  const [mode, setMode] = useState<'ai' | 'manual'>('ai');
  const [prompt, setPrompt] = useState('');
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState<any>(null);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  // Manual mode state
  const [manualName, setManualName] = useState('');
  const [manualDesc, setManualDesc] = useState('');
  const [manualFields, setManualFields] = useState<any[]>([]);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setGenerating(true);
    setError('');
    try {
      const data = await apiPost('/scenarios/generate', { prompt });
      setGenerated(data);
    } catch (err: any) {
      setError(err.message || 'AI 生成失败，请重试或切换到手动模式');
    }
    setGenerating(false);
  };

  const handleSaveGenerated = async () => {
    if (!generated) return;
    setSaving(true);
    try {
      await apiPost('/scenarios', generated);
      onCreated();
    } catch (err: any) {
      setError(err.message || '保存失败');
    }
    setSaving(false);
  };

  const handleSaveManual = async () => {
    setSaving(true);
    try {
      const scenarioData = {
        name: manualName,
        description: manualDesc,
        form_schema: { fields: manualFields },
        match_config: {
          embedding_source: 'composite',
          embedding_fields: manualFields
            .filter((f: any) => f.type === 'textarea' || f.type === 'text')
            .map((f: any) => f.key),
          filter_fields: [],
          weight_fields: {},
          top_k: 10,
          min_similarity: 0.7,
        },
        ui_config: {
          theme_color: '#1a1a2e',
          card_layout: 'grid',
          result_display: manualFields.map((f: any) => f.key),
        },
      };
      await apiPost('/scenarios', scenarioData);
      onCreated();
    } catch (err: any) {
      setError(err.message || '保存失败');
    }
    setSaving(false);
  };

  const addManualField = () => {
    setManualFields([...manualFields, { key: '', type: 'text', label: '', required: true }]);
  };

  const updateManualField = (index: number, field: any) => {
    const updated = [...manualFields];
    updated[index] = { ...updated[index], ...field };
    setManualFields(updated);
  };

  const removeManualField = (index: number) => {
    setManualFields(manualFields.filter((_, i) => i !== index));
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">创建匹配场景</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
        </div>

        <div className="p-6">
          {/* Mode Toggle */}
          <div className="flex gap-2 mb-6">
            <button
              onClick={() => setMode('ai')}
              className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                mode === 'ai'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              🤖 AI 智能生成
            </button>
            <button
              onClick={() => setMode('manual')}
              className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                mode === 'manual'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              ✏️ 手动创建
            </button>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
              {error}
            </div>
          )}

          {/* AI Mode */}
          {mode === 'ai' && !generated && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                用自然语言描述你想要的匹配场景
              </label>
              <textarea
                value={prompt}
                onChange={e => setPrompt(e.target.value)}
                placeholder="例如：我想要一个王者荣耀队友匹配，需要玩家填写段位、擅长分路、胜率、游戏风格自我介绍..."
                rows={5}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                disabled={generating}
              />
              <button
                onClick={handleGenerate}
                disabled={generating || !prompt.trim()}
                className="mt-4 w-full py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {generating ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
                    AI 正在分析需求...
                  </span>
                ) : (
                  '✨ AI 生成场景配置'
                )}
              </button>
            </div>
          )}

          {/* AI Generated Preview — NOW EDITABLE */}
          {mode === 'ai' && generated && (
            <div className="space-y-4">
              <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3 text-sm text-indigo-700">
                🤖 AI 已生成草稿，你可以直接修改下方所有字段，然后保存。
              </div>

              {/* Editable name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">场景名称 *</label>
                <input
                  type="text"
                  value={generated.name}
                  onChange={e => setGenerated({ ...generated, name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              {/* Editable description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">场景描述</label>
                <textarea
                  value={generated.description}
                  onChange={e => setGenerated({ ...generated, description: e.target.value })}
                  rows={2}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              {/* Editable fields */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700">表单字段</label>
                  <button
                    type="button"
                    onClick={() => {
                      const fields = [...(generated.form_schema?.fields || [])];
                      fields.push({ key: '', type: 'text', label: '', required: true });
                      setGenerated({ ...generated, form_schema: { ...generated.form_schema, fields } });
                    }}
                    className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
                  >+ 添加字段</button>
                </div>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {(generated.form_schema?.fields || []).map((field: any, i: number) => (
                    <div key={i} className="flex gap-2 items-center bg-gray-50 rounded-lg p-2 border border-gray-200">
                      <input
                        value={field.key}
                        onChange={e => {
                          const fields = [...generated.form_schema.fields];
                          fields[i] = { ...fields[i], key: e.target.value };
                          setGenerated({ ...generated, form_schema: { ...generated.form_schema, fields } });
                        }}
                        placeholder="key"
                        className="w-20 px-2 py-1 border border-gray-300 rounded text-xs"
                      />
                      <input
                        value={field.label}
                        onChange={e => {
                          const fields = [...generated.form_schema.fields];
                          fields[i] = { ...fields[i], label: e.target.value };
                          setGenerated({ ...generated, form_schema: { ...generated.form_schema, fields } });
                        }}
                        placeholder="标签"
                        className="flex-1 px-2 py-1 border border-gray-300 rounded text-xs"
                      />
                      <select
                        value={field.type}
                        onChange={e => {
                          const fields = [...generated.form_schema.fields];
                          fields[i] = { ...fields[i], type: e.target.value };
                          setGenerated({ ...generated, form_schema: { ...generated.form_schema, fields } });
                        }}
                        className="w-24 px-1 py-1 border border-gray-300 rounded text-xs"
                      >
                        <option value="text">text</option>
                        <option value="textarea">textarea</option>
                        <option value="number">number</option>
                        <option value="select">select</option>
                        <option value="multi_select">multi</option>
                        <option value="slider">slider</option>
                        <option value="date">date</option>
                        <option value="contact">contact</option>
                      </select>
                      <label className="flex items-center gap-1 text-xs">
                        <input
                          type="checkbox"
                          checked={field.required}
                          onChange={e => {
                            const fields = [...generated.form_schema.fields];
                            fields[i] = { ...fields[i], required: e.target.checked };
                            setGenerated({ ...generated, form_schema: { ...generated.form_schema, fields } });
                          }}
                        />必填
                      </label>
                      <button
                        type="button"
                        onClick={() => {
                          const fields = generated.form_schema.fields.filter((_: any, j: number) => j !== i);
                          setGenerated({ ...generated, form_schema: { ...generated.form_schema, fields } });
                        }}
                        className="text-red-400 hover:text-red-600 text-sm"
                      >✕</button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Collapsible match_config */}
              <details className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                <summary className="text-sm font-medium text-gray-700 cursor-pointer">匹配配置 ▼</summary>
                <div className="mt-3 grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-gray-500">Top K</label>
                    <input type="number" value={generated.match_config?.top_k || 10}
                      onChange={e => setGenerated({ ...generated, match_config: { ...generated.match_config, top_k: parseInt(e.target.value) || 10 } })}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-xs" />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500">最低相似度</label>
                    <input type="number" step="0.1" value={generated.match_config?.min_similarity || 0.7}
                      onChange={e => setGenerated({ ...generated, match_config: { ...generated.match_config, min_similarity: parseFloat(e.target.value) || 0.7 } })}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-xs" />
                  </div>
                </div>
              </details>

              {/* Collapsible ui_config */}
              <details className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                <summary className="text-sm font-medium text-gray-700 cursor-pointer">界面配置 ▼</summary>
                <div className="mt-3 grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-gray-500">主题色</label>
                    <input type="color" value={generated.ui_config?.theme_color || '#4f46e5'}
                      onChange={e => setGenerated({ ...generated, ui_config: { ...generated.ui_config, theme_color: e.target.value } })}
                      className="w-full h-8 border border-gray-300 rounded" />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500">卡片布局</label>
                    <select value={generated.ui_config?.card_layout || 'grid'}
                      onChange={e => setGenerated({ ...generated, ui_config: { ...generated.ui_config, card_layout: e.target.value } })}
                      className="w-full px-2 py-1 border border-gray-300 rounded text-xs">
                      <option value="grid">网格</option>
                      <option value="list">列表</option>
                    </select>
                  </div>
                </div>
              </details>

              {/* Action buttons */}
              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => setGenerated(null)}
                  className="flex-1 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm hover:bg-gray-50"
                >重新生成</button>
                <button
                  onClick={handleSaveGenerated}
                  disabled={saving}
                  className="flex-1 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
                >{saving ? '保存中...' : '保存并发布场景'}</button>
              </div>
            </div>
          )}

          {/* Manual Mode */}
          {mode === 'manual' && (
            <div>
              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">场景名称 *</label>
                  <input
                    type="text"
                    value={manualName}
                    onChange={e => setManualName(e.target.value)}
                    placeholder="如：2024 王者荣耀队友匹配"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">场景描述</label>
                  <textarea
                    value={manualDesc}
                    onChange={e => setManualDesc(e.target.value)}
                    rows={2}
                    placeholder="简要描述这个匹配场景的目的..."
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              {/* Fields */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-gray-700">表单字段</label>
                  <button
                    onClick={addManualField}
                    className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
                  >
                    + 添加字段
                  </button>
                </div>
                <div className="space-y-3">
                  {manualFields.map((field: any, i: number) => (
                    <div key={i} className="flex gap-2 items-start bg-gray-50 rounded-lg p-3 border border-gray-200">
                      <input
                        type="text"
                        value={field.key}
                        onChange={e => updateManualField(i, { key: e.target.value })}
                        placeholder="字段 key"
                        className="w-24 px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                      <input
                        type="text"
                        value={field.label}
                        onChange={e => updateManualField(i, { label: e.target.value })}
                        placeholder="显示标签"
                        className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm"
                      />
                      <select
                        value={field.type}
                        onChange={e => updateManualField(i, { type: e.target.value })}
                        className="w-24 px-2 py-1 border border-gray-300 rounded text-sm"
                      >
                        <option value="text">text</option>
                        <option value="textarea">textarea</option>
                        <option value="number">number</option>
                        <option value="select">select</option>
                        <option value="multi_select">multi_select</option>
                      </select>
                      <label className="flex items-center gap-1 text-xs">
                        <input
                          type="checkbox"
                          checked={field.required}
                          onChange={e => updateManualField(i, { required: e.target.checked })}
                        />
                        必填
                      </label>
                      <button
                        onClick={() => removeManualField(i)}
                        className="text-red-400 hover:text-red-600 text-sm"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <button
                onClick={handleSaveManual}
                disabled={saving || !manualName.trim() || manualFields.length === 0}
                className="w-full py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {saving ? '保存中...' : '保存场景'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

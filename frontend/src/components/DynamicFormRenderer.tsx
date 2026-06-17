'use client';

import { useState } from 'react';

interface FormField {
  key: string;
  type: string;
  label: string;
  required?: boolean;
  placeholder?: string;
  options?: string[];
  min?: number;
  max?: number;
  step?: number;
}

interface Props {
  formSchema: { fields: FormField[] };
  onSubmit: (formData: Record<string, any>) => Promise<void>;
  submitLabel?: string;
  submitting?: boolean;
  initialValues?: Record<string, any>;
}

export default function DynamicFormRenderer({
  formSchema,
  onSubmit,
  submitLabel = '提交',
  submitting = false,
  initialValues,
}: Props) {
  const [formData, setFormData] = useState<Record<string, any>>(initialValues || {});
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleChange = (key: string, value: any) => {
    setFormData(prev => ({ ...prev, [key]: value }));
    // Clear error on change
    if (errors[key]) {
      setErrors(prev => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
    }
  };

  const handleMultiSelect = (key: string, option: string) => {
    const current = formData[key] || [];
    if (current.includes(option)) {
      handleChange(key, current.filter((v: string) => v !== option));
    } else {
      handleChange(key, [...current, option]);
    }
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    for (const field of formSchema.fields) {
      if (field.required) {
        const value = formData[field.key];
        if (value === undefined || value === null || value === '') {
          newErrors[field.key] = `${field.label} 为必填项`;
        } else if (field.type === 'multi_select' && Array.isArray(value) && value.length === 0) {
          newErrors[field.key] = `请至少选择一项 ${field.label}`;
        }
      }
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    await onSubmit(formData);
  };

  const renderField = (field: FormField) => {
    const value = formData[field.key];
    const error = errors[field.key];

    const baseInputClass = `w-full px-4 py-2.5 border rounded-lg text-sm transition-colors ${
      error
        ? 'border-red-300 bg-red-50 focus:ring-red-500'
        : 'border-gray-300 focus:ring-indigo-500 focus:border-indigo-500'
    } focus:outline-none focus:ring-2`;

    switch (field.type) {
      case 'contact':
        return (
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-lg">📞</span>
            <input
              type="text"
              value={value || ''}
              onChange={e => handleChange(field.key, e.target.value)}
              placeholder={field.placeholder || '微信号 / 手机号 / QQ号'}
              className={`${baseInputClass} pl-10 border-green-300 focus:ring-green-500 focus:border-green-500`}
            />
          </div>
        );

      case 'text':
        return (
          <input
            type="text"
            value={value || ''}
            onChange={e => handleChange(field.key, e.target.value)}
            placeholder={field.placeholder || `请输入${field.label}`}
            className={baseInputClass}
          />
        );

      case 'textarea':
        return (
          <textarea
            value={value || ''}
            onChange={e => handleChange(field.key, e.target.value)}
            placeholder={field.placeholder || `请描述${field.label}`}
            rows={4}
            className={`${baseInputClass} resize-none`}
          />
        );

      case 'number':
        return (
          <input
            type="number"
            value={value ?? ''}
            onChange={e => handleChange(field.key, parseFloat(e.target.value) || '')}
            min={field.min}
            max={field.max}
            step={field.step}
            placeholder={field.placeholder}
            className={baseInputClass}
          />
        );

      case 'select':
        return (
          <select
            value={value || ''}
            onChange={e => handleChange(field.key, e.target.value)}
            className={baseInputClass}
          >
            <option value="">-- 请选择 --</option>
            {field.options?.map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        );

      case 'multi_select':
        return (
          <div className="flex flex-wrap gap-2">
            {field.options?.map(opt => {
              const selected = (value || []).includes(opt);
              return (
                <button
                  key={opt}
                  type="button"
                  onClick={() => handleMultiSelect(field.key, opt)}
                  className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${
                    selected
                      ? 'bg-indigo-600 text-white border-indigo-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:border-indigo-400'
                  }`}
                >
                  {opt}
                </button>
              );
            })}
          </div>
        );

      case 'slider':
        return (
          <div className="flex items-center gap-3">
            <input
              type="range"
              value={value || field.min || 0}
              onChange={e => handleChange(field.key, parseInt(e.target.value))}
              min={field.min || 0}
              max={field.max || 100}
              step={field.step || 1}
              className="flex-1"
            />
            <span className="text-sm font-mono text-gray-700 w-12 text-right">
              {value || field.min || 0}
            </span>
          </div>
        );

      default:
        return (
          <input
            type="text"
            value={value || ''}
            onChange={e => handleChange(field.key, e.target.value)}
            className={baseInputClass}
          />
        );
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {formSchema.fields.map(field => (
        <div key={field.key}>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            {field.label}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </label>
          {renderField(field)}
          {errors[field.key] && (
            <p className="mt-1 text-sm text-red-600">{errors[field.key]}</p>
          )}
        </div>
      ))}
      <button
        type="submit"
        disabled={submitting}
        className="w-full py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-md"
      >
        {submitting ? (
          <span className="flex items-center justify-center gap-2">
            <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
            提交中...
          </span>
        ) : (
          submitLabel
        )}
      </button>
    </form>
  );
}

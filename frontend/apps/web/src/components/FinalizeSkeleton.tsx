import React from 'react';
import { Skeleton } from 'antd';

const STAGE_LABEL: Record<string, string> = {
  calling_llm: 'Generating brief',
  validating: 'Validating structure',
  persisting: 'Saving workspace',
  done: 'Ready to review',
};

export const FinalizeStageIndicator: React.FC<{ stage: string | null }> = ({ stage }) => {
  const steps = ['calling_llm', 'validating', 'persisting'] as const;
  const idx = stage ? steps.indexOf(stage as typeof steps[number]) : -1;
  const active = stage === 'done' ? steps.length : Math.max(0, idx);
  return (
    <div style={{ display: 'flex', gap: 8, padding: '12px 14px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, marginBottom: 12 }}>
      {steps.map((s, i) => {
        const done = i < active || stage === 'done';
        const cur = i === idx && stage !== 'done';
        return (
          <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1 }}>
            <span style={{
              width: 22, height: 22, borderRadius: 999, display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: done ? '#2563eb' : cur ? '#dbeafe' : '#f1f5f9',
              color: done ? '#fff' : cur ? '#2563eb' : '#94a3b8',
              fontSize: 11, fontWeight: 700, border: cur ? '1px solid #93c5fd' : 'none',
              animation: cur ? 'pulse 1.6s infinite' : undefined,
            }}>{done ? '✓' : i + 1}</span>
            <span style={{ fontSize: 11, fontWeight: cur ? 700 : 500, color: cur ? '#1d4ed8' : done ? '#0f172a' : '#94a3b8' }}>{STAGE_LABEL[s]}</span>
            {i < steps.length - 1 && <span style={{ flex: 1, height: 2, background: done ? '#bfdbfe' : '#e2e8f0', borderRadius: 2, margin: '0 6px' }} />}
          </div>
        );
      })}
    </div>
  );
};

export const FinalizeSkeleton: React.FC<{ stage: string | null }> = ({ stage }) => (
  <div className="np-requirements" style={{ opacity: 0.95 }}>
    <FinalizeStageIndicator stage={stage} />
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <Skeleton.Input active block style={{ height: 22 }} />
      <Skeleton active paragraph={{ rows: 2 }} />
      {[1, 2, 3, 4].map((k) => (
        <div key={k} style={{ border: '1px solid #e2e8f0', borderRadius: 8, padding: 14, background: '#fff' }}>
          <Skeleton.Input active size="small" style={{ width: 160, marginBottom: 10 }} />
          <Skeleton active paragraph={{ rows: 2 }} />
        </div>
      ))}
      <div style={{ border: '1px solid #bfdbfe', borderRadius: 8, padding: 14, background: '#fff' }}>
        <Skeleton.Input active size="small" style={{ width: 140, marginBottom: 10 }} />
        {[1, 2, 3].map((k) => (
          <div key={k} style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 8 }}>
            <Skeleton.Avatar active size="small" shape="circle" />
            <Skeleton.Input active size="small" style={{ flex: 1 }} />
          </div>
        ))}
      </div>
    </div>
  </div>
);

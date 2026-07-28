import React from 'react';
import { ApiClient } from '../api/client';

type ProjectWorkBoardProps = {
  projectId: string;
};

const columns = ['TO DO', 'IN PROGRESS', 'IN REVIEW', 'DONE'] as const;

export function ProjectWorkBoard({ projectId }: ProjectWorkBoardProps) {
  React.useEffect(() => {
    ApiClient.get(`/projects/${projectId}/work-board`).catch(() => {});
  }, [projectId]);

  return (
    <div
      style={{
        minHeight: '100%',
        background: '#FFFFFF',
        padding: 24,
        display: 'grid',
        gridTemplateColumns: 'repeat(4, minmax(220px, 1fr))',
        gap: 18,
        overflowX: 'auto',
      }}
    >
      {columns.map((label) => (
        <section
          key={label}
          style={{
            minHeight: 460,
            borderRadius: 8,
            background: '#F7F8FA',
            padding: 22,
            boxSizing: 'border-box',
          }}
        >
          <div
            style={{
              color: '#4B5563',
              fontSize: 12,
              fontWeight: 700,
              letterSpacing: 0,
              textTransform: 'uppercase',
              display: 'flex',
              alignItems: 'center',
              gap: 7,
            }}
          >
            <span>{label}</span>
            {label === 'DONE' && (
              <span
                aria-hidden="true"
                style={{
                  width: 15,
                  height: 15,
                  borderRadius: '50%',
                  background: '#22C55E',
                  color: '#FFFFFF',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 10,
                  lineHeight: 1,
                  fontWeight: 800,
                }}
              >
                ✓
              </span>
            )}
          </div>
        </section>
      ))}
    </div>
  );
}

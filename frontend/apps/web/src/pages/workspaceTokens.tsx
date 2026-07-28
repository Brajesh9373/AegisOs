import React from 'react';

export const ui = {
  color: {
    bg: '#F8FAFC',
    surface: '#FFFFFF',
    surfaceMuted: '#F1F5F9',
    border: '#E2E8F0',
    borderStrong: '#CBD5E1',
    text: '#0F172A',
    textMuted: '#64748B',
    textFaint: '#94A3B8',
    primary: '#2563EB',
    primarySoft: '#EFF6FF',
    violet: '#7C3AED',
    violetSoft: '#F5F3FF',
    success: '#16A34A',
    successSoft: '#F0FDF4',
    warning: '#D97706',
    warningSoft: '#FFFBEB',
    danger: '#DC2626',
    dangerSoft: '#FEF2F2',
  },
  radius: {
    sm: 6,
    md: 8,
    pill: 999,
  },
  shadow: {
    xs: '0 1px 2px rgba(15, 23, 42, 0.04)',
    sm: '0 1px 3px rgba(15, 23, 42, 0.08)',
  },
} as const;

type WorkspaceStatus = 'RUNNING' | 'WAITING' | 'BLOCKED' | 'COMPLETED';

export const STATUS_STYLE: Record<WorkspaceStatus, {
  label: string;
  bg: string;
  dot: string;
  text: string;
}> = {
  RUNNING: {
    label: 'Running',
    bg: '#EFF6FF',
    dot: '#2563EB',
    text: '#1D4ED8',
  },
  WAITING: {
    label: 'Waiting',
    bg: '#F8FAFC',
    dot: '#94A3B8',
    text: '#64748B',
  },
  BLOCKED: {
    label: 'Blocked',
    bg: '#FEF2F2',
    dot: '#DC2626',
    text: '#B91C1C',
  },
  COMPLETED: {
    label: 'Complete',
    bg: '#F0FDF4',
    dot: '#16A34A',
    text: '#15803D',
  },
};

export const SectionLabel: React.FC<React.HTMLAttributes<HTMLSpanElement>> = ({
  children,
  style,
  ...props
}) => (
  <span
    {...props}
    style={{
      display: 'block',
      color: ui.color.textFaint,
      fontSize: 10,
      fontWeight: 700,
      letterSpacing: 0.4,
      textTransform: 'uppercase',
      ...style,
    }}
  >
    {children}
  </span>
);

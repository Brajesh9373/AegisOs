import React from 'react';
import { Typography } from 'antd';
import { colors } from '../../theme/colors';

const { Text } = Typography;

interface MetricCardProps {
  label: string;
  value: React.ReactNode;
}

export const MetricCard: React.FC<MetricCardProps> = ({ label, value }) => {
  return (
    <div style={{ background: '#F8FAFC', padding: '12px 16px', border: `1px solid ${colors.border}` }}>
      <Text style={{ color: colors.textSecondary, fontSize: '9px', display: 'block', textTransform: 'uppercase' }}>{label}</Text>
      <Text strong style={{ color: colors.textPrimary, fontSize: '13px', display: 'block', marginTop: 4 }}>{value}</Text>
    </div>
  );
};

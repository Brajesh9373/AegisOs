import React from 'react';
import { Card, Statistic } from 'antd';
import { colors } from '../../theme/colors';

interface ExecutiveCardProps {
  title: string;
  value: string | number;
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
  bg?: string;
  borderColor?: string;
  valueColor?: string;
}

export const ExecutiveCard: React.FC<ExecutiveCardProps> = ({ title, value, prefix, suffix, bg = '#FFFFFF', borderColor = '#E5E7EB', valueColor = '#FFFFFF' }) => {
  return (
    <Card 
      style={{ 
        background: bg, 
        border: `1px solid ${borderColor}`,
        marginBottom: 20
      }} 
      bodyStyle={{ padding: '20px 24px' }}
      bordered={false}
    >
      <Statistic 
        title={<span style={{ color: colors.textSecondary, fontSize: '11px', fontWeight: 600, letterSpacing: '0.5px' }}>{title.toUpperCase()}</span>} 
        value={value} 
        valueStyle={{ color: valueColor, fontWeight: 800, fontSize: '28px', lineHeight: 1 }} 
        prefix={prefix} 
        suffix={suffix}
      />
    </Card>
  );
};

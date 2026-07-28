import React from 'react';
import { Space, Typography } from 'antd';
import { colors } from '../../theme/colors';

const { Text } = Typography;

interface PanelHeaderProps {
  title: string;
  icon?: React.ReactNode;
  extra?: React.ReactNode;
}

export const PanelHeader: React.FC<PanelHeaderProps> = ({ title, icon, extra }) => {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: `1px solid ${colors.border}`, padding: '12px 16px', background: colors.secondarySurface }}>
      <Space>
        {icon}
        <Text strong style={{ color: colors.textPrimary, fontSize: '13px' }}>{title.toUpperCase()}</Text>
      </Space>
      {extra}
    </div>
  );
};

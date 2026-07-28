import React from 'react';
import { Space } from 'antd';
import { colors } from '../../theme/colors';

interface ActionToolbarProps {
  children: React.ReactNode;
  extra?: React.ReactNode;
}

export const ActionToolbar: React.FC<ActionToolbarProps> = ({ children, extra }) => {
  return (
    <div style={{ background: colors.surface, border: `1px solid ${colors.border}`, padding: '12px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
      <Space size="middle">
        {children}
      </Space>
      {extra}
    </div>
  );
};

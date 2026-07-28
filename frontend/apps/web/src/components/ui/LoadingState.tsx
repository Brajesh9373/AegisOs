import React from 'react';
import { Spin } from 'antd';
import { colors } from '../../theme/colors';

export const LoadingState: React.FC = () => {
  return (
    <div style={{ height: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center', background: colors.background }}>
      <Spin size="large" />
    </div>
  );
};

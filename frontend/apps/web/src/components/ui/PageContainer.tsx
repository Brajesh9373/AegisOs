import React from 'react';
import { colors } from '../../theme/colors';

interface PageContainerProps {
  children: React.ReactNode;
  maxWidth?: number;
}

export const PageContainer: React.FC<PageContainerProps> = ({ children, maxWidth = 1600 }) => {
  return (
    <div style={{ background: colors.background, minHeight: '100vh', padding: '32px 32px', color: colors.textPrimary }}>
      <div style={{ maxWidth, margin: '0 auto' }}>
        {children}
      </div>
    </div>
  );
};

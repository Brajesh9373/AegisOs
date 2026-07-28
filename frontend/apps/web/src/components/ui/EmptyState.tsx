import React from 'react';
import { Empty } from 'antd';
import { colors } from '../../theme/colors';

interface EmptyStateProps {
  description?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ description = 'No data active in this scope' }) => {
  return (
    <div style={{ textAlign: 'center', padding: '32px 0' }}>
      <Empty description={<span style={{ color: colors.textSecondary, fontSize: '12px' }}>{description}</span>} />
    </div>
  );
};

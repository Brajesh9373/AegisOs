import React from 'react';
import { Typography } from 'antd';
import { colors } from '../../theme/colors';

const { Text } = Typography;

interface SectionHeaderProps {
  title: string;
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({ title }) => {
  return (
    <div style={{ marginBottom: 12 }}>
      <Text style={{ fontSize: '11px', fontWeight: 600, color: colors.textSecondary, textTransform: 'uppercase', letterSpacing: '1px' }}>
        {title}
      </Text>
    </div>
  );
};

import React from 'react';
import { Card } from 'antd';
import { colors } from '../../theme/colors';
import { shadows } from '../../theme/shadows';

interface PanelProps {
  children: React.ReactNode;
  style?: React.CSSProperties;
  bodyStyle?: React.CSSProperties;
  bordered?: boolean;
}

export const Panel: React.FC<PanelProps> = ({ children, style, bodyStyle, bordered = true }) => {
  return (
    <Card
      style={{
        background: colors.surface,
        border: bordered ? `1px solid ${colors.border}` : 'none',
        borderRadius: 12,
        boxShadow: shadows.panel,
        marginBottom: 20,
        ...style
      }}
      bodyStyle={bodyStyle}
      bordered={false}
    >
      {children}
    </Card>
  );
};

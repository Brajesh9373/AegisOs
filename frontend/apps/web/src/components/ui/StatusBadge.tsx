import React from 'react';
import { Tag } from 'antd';

interface StatusBadgeProps {
  status: string;
  text?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, text }) => {
  const normalized = status.toLowerCase();
  let color = 'default';
  if (normalized === 'running' || normalized === 'active' || normalized === 'completed') {
    color = 'green';
  } else if (normalized === 'blocked' || normalized === 'failed') {
    color = 'red';
  } else if (normalized === 'planning' || normalized === 'blue') {
    color = 'blue';
  } else if (normalized === 'waiting' || normalized === 'queued') {
    color = 'orange';
  }
  
  return (
    <Tag color={color} style={{  borderRadius: 0, fontSize: '10px', fontWeight: 600, margin: 0 }}>
      {text ? text.toUpperCase() : status.toUpperCase()}
    </Tag>
  );
};

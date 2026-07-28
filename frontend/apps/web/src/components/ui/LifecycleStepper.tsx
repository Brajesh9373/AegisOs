import React from 'react';
import { Steps } from 'antd';

interface LifecycleStepperProps {
  currentStage: string;
}

export const LifecycleStepper: React.FC<LifecycleStepperProps> = ({ currentStage }) => {
  const stages = [
    'Lead',
    'Qualified',
    'Discovery',
    'RFQ',
    'Proposal',
    'Approval',
    'Initialization',
    'Project',
    'Execution',
    'Completed'
  ];

  const currentIndex = stages.indexOf(currentStage);

  return (
    <div style={{ padding: '16px 24px', background: '#FFFFFF', borderBottom: '1px solid #f0f0f0', marginBottom: 24 }}>
      <Steps 
        size="small" 
        current={currentIndex}
        items={stages.map((stage, idx) => ({
          key: stage,
          title: stage,
          status: idx < currentIndex ? 'finish' : (idx === currentIndex ? 'process' : 'wait')
        }))}
      />
    </div>
  );
};

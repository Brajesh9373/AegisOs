import React, { createContext, useContext, useState, ReactNode } from 'react';

export type LifecycleState = {
  customer: any;
  opportunity: any;
  project: any;
  workspace: any;
};

type LifecycleContextType = {
  state: LifecycleState;
  updateState: (updates: Partial<LifecycleState>) => void;
  createProjectFromInitialization: (id: string) => void;
};

const LifecycleContext = createContext<LifecycleContextType | undefined>(undefined);

export const LifecycleProvider = ({ children }: { children: ReactNode }) => {
  const [state, setState] = useState<LifecycleState>({
    customer: { id: 'cust-demo', company: 'VNU', industry: 'Manufacturing', status: 'Active' },
    opportunity: { id: 'demo', title: 'Global Database Migration', value: '$250,000', status: 'Approval' },
    project: null,
    workspace: null
  });

  const updateState = (updates: Partial<LifecycleState>) => {
    setState(prev => ({ ...prev, ...updates }));
  };

  const createProjectFromInitialization = (id: string) => {
    const projectId = `proj-${Date.now()}`;
    const workspaceId = `ws-${Date.now()}`;
    
    updateState({
      project: {
        id: projectId,
        customerId: state.customer?.id || 'cust-demo',
        opportunityId: id,
        workspaceId: workspaceId,
        name: state.opportunity?.title || 'Global Database Migration',
        type: 'Migration',
        priority: 'High',
        summary: 'Automated workflow execution for ' + (state.opportunity?.title || 'Migration'),
        goal: 'Accelerate delivery timelines.',
        customer: state.customer?.company || 'VNU',
        budget: state.opportunity?.value || '$250,000',
        status: 'Active',
        stage: 'Execution',
        progress: 0,
        workspaceReady: true,
        health: { status: 'Green', score: 100, risks: 0, blocked: 0, approvals: 0 },
        owner: 'Current User',
        lastActivity: 'Just now',
        sustainability: { tokens: '0', cost: '$0.00', co2: '0.00kg', water: '0.0L', energy: '0.00 kWh', trees: 0, updated: 'Just now' },
        createdAt: new Date().toLocaleDateString(),
        initializedAt: new Date().toLocaleDateString()
      },
      workspace: {
        id: workspaceId,
        status: 'Ready'
      }
    });
  };

  return (
    <LifecycleContext.Provider value={{ state, updateState, createProjectFromInitialization }}>
      {children}
    </LifecycleContext.Provider>
  );
};

export const useLifecycle = () => {
  const context = useContext(LifecycleContext);
  if (!context) throw new Error('useLifecycle must be used within LifecycleProvider');
  return context;
};

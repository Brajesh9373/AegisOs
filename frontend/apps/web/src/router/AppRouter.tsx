
import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from '../layout/AppLayout';
import { Login } from '../pages/Login';
import { InstallWizard } from '../pages/InstallWizard';
import { Users } from '../pages/Users';
import { ApiClient } from '../api/client';
import { OperationsConsole } from '../pages/OperationsConsole';
import { Dashboard } from '../pages/Dashboard';
import { CustomerRegistry } from '../pages/CustomerRegistry';
import { CustomerDetails } from '../pages/CustomerDetails';
import { OpportunityPipeline } from '../pages/OpportunityPipeline';
import { OpportunityDetails } from '../pages/OpportunityDetails';
import { NewOpportunityWizard } from '../pages/NewOpportunityWizard';
import { OpportunityApproval } from '../pages/OpportunityApproval';
import { ProjectWorkspace } from '../pages/ProjectWorkspace';
import { HumanQueue } from '../pages/HumanQueue';
import { ProjectsList } from '../pages/ProjectsList';
import { NewProject } from '../pages/NewProject';
import { Notifications } from '../pages/Notifications';
import { Artifacts } from '../pages/Artifacts';
import { Administration } from '../pages/Administration';
import { UploadRFP } from '../pages/UploadRFP';
import { GeneralAIDiscovery } from '../pages/GeneralAIDiscovery';
import { RFQBuilder } from '../pages/RFQBuilder';
import { BudgetEstimation } from '../pages/BudgetEstimation';
import { Proposal } from '../pages/Proposal';
import { ProjectInitialization } from '../pages/ProjectInitialization';
import { AgentProfiles } from '../pages/AgentProfiles';

function ProtectedRoute({ children, requiredRole }: { children: React.ReactNode, requiredRole?: string }) {
  const [auth, setAuth] = useState<{ allowed: boolean, loading: boolean }>({ allowed: false, loading: true });

  useEffect(() => {
    ApiClient.get('/auth/me').then(res => {
      if (requiredRole) {
        ApiClient.post('/rbac/evaluate', { role: res.user.role, resource: 'general', action: 'view' })
          .then(rbac => setAuth({ allowed: rbac.allowed, loading: false }))
          .catch(() => setAuth({ allowed: false, loading: false }));
      } else {
        setAuth({ allowed: true, loading: false });
      }
    }).catch(() => setAuth({ allowed: false, loading: false }));
  }, [requiredRole]);

  if (auth.loading) return <div>Loading...</div>;
  if (!auth.allowed) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export function AppRouter() {
  const [locked, setLocked] = useState<boolean | null>(null);

  useEffect(() => {
    ApiClient.get('/installation/status')
      .then(res => setLocked(res.locked))
      .catch(() => setLocked(false));
  }, []);

  if (locked === null) return <div>Loading...</div>;

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/install" element={locked ? <Navigate to="/login" /> : <InstallWizard onComplete={() => setLocked(true)} />} />
        
        <Route path="/" element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
          <Route index element={<Navigate to="/home" replace />} />
          <Route path="home" element={<Dashboard />} />
          <Route path="users" element={<ProtectedRoute requiredRole="Org Admin"><Users /></ProtectedRoute>} />
          <Route path="customers" element={<CustomerRegistry />} />
          <Route path="customers/:id" element={<CustomerDetails />} />
          <Route path="opportunities" element={<OpportunityPipeline />} />
          <Route path="opportunities/new" element={<NewOpportunityWizard />} />
          <Route path="opportunities/:id" element={<OpportunityDetails />} />
          <Route path="opportunities/:id/rfp" element={<Navigate to="../" replace />} />
          <Route path="opportunities/:id/discovery" element={<GeneralAIDiscovery />} />
          <Route path="opportunities/:id/rfq" element={<RFQBuilder />} />
          <Route path="opportunities/:id/budget" element={<BudgetEstimation />} />
          <Route path="opportunities/:id/proposal" element={<Proposal />} />
          <Route path="opportunities/:id/approve" element={<OpportunityApproval />} />
          <Route path="opportunities/:id/init" element={<ProjectInitialization />} />
          <Route path="projects" element={<ProjectsList />} />
          <Route path="projects/:id" element={<Navigate to="workspace" replace />} />
          <Route path="queue" element={<HumanQueue />} />
          <Route path="notifications" element={<Notifications />} />
          <Route path="artifacts" element={<Artifacts />} />
          <Route path="administration" element={<Administration />} />
          <Route path="agent-profiles" element={<AgentProfiles />} />
        </Route>
        
        <Route path="/projects/:id/workspace" element={<ProtectedRoute><ProjectWorkspace /></ProtectedRoute>} />
        <Route path="/projects/new" element={<ProtectedRoute><NewProject /></ProtectedRoute>} />
      </Routes>
    </BrowserRouter>
  );
}

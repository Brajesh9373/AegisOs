export interface TemplateBinding {
  templateId: string;
}

export interface BusinessGoalBinding {
  goalId: string;
}

export interface CustomerBinding {
  customerId: string;
}

export interface ProjectBinding {
  projectId: string;
}

export interface WorkflowBinding {
  workflowId: string;
}

export interface AgentBinding {
  agentId: string;
}

export interface SkillBinding {
  skillId: string;
}

export interface ToolBinding {
  toolId: string;
}

export interface ProviderBinding {
  providerId: string;
}

export interface EnvironmentBinding {
  environmentId: string;
}

export interface VariableBinding {
  variables: Record<string, unknown>;
}

export interface SecretBinding {
  secrets: string[];
}

export interface ConfigurationBinding {
  configOverrides: Record<string, unknown>;
}

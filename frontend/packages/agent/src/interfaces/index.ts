export interface IAgentMemory {
  store(key: string, value: unknown): Promise<void>;
  retrieve(key: string): Promise<unknown | null>;
  clear(): Promise<void>;
}

export interface IAgentSupervisor {
  assignTask(agentId: string, taskId: string): Promise<void>;
  requestApproval(agentId: string, data: unknown): Promise<boolean>;
}

export interface IAgentCommunication {
  sendMessage(toAgentId: string, message: unknown): Promise<void>;
  receiveMessage(fromAgentId: string, message: unknown): Promise<void>;
}

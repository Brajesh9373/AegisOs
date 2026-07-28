import { RuntimeBootstrap } from '@aegisos/runtime-host';
import { PluginLoader, PluginRegistry, PluginType } from '@aegisos/plugin-loader';
import { ExecutionEngine } from '@aegisos/execution-runtime';
import { WorkflowScheduler, WorkflowDefinition, WorkflowState } from '@aegisos/workflow-runtime';
import { AgentRuntime, AgentState } from '@aegisos/agent-runtime';
import { TeamRuntime } from '@aegisos/multi-agent-runtime';

async function bootstrap() {
  console.log('[E2E] Starting Platform Bootstrap Sequence...');
  const t0 = performance.now();

  // 1. Core Boot
  const host = new RuntimeBootstrap();
  await host.start({ environment: 'e2e' });
  console.log('  -> RuntimeHost Started');

  // 2. Plugin Loading
  const registry = new PluginRegistry();
  const loader = new PluginLoader(registry);
  await loader.load({
    id: 'mock-plugin',
    name: 'Mock Plugin',
    version: '1.0.0',
    type: PluginType.Tool,
    dependencies: {},
    capabilities: [],
  });
  console.log('  -> PluginLoader Initialized');

  // 3. Execution Engine
  const engine = new ExecutionEngine();
  console.log('  -> Execution Engine Ready');

  // 4. Workflow Scheduling
  const scheduler = new WorkflowScheduler(engine);
  const demoWf: WorkflowDefinition = {
    id: 'wf-demo-e2e',
    nodes: [
      { id: 'start-node', type: 'trigger', config: {} },
      { id: 'agent-eval-node', type: 'task', config: {} },
    ],
    edges: [{ source: 'start-node', target: 'agent-eval-node' }],
  };
  console.log('  -> Workflow Definition Registered');

  // 5. Agent Invocation
  const agentRuntime = new AgentRuntime();
  console.log('  -> Agent Runtime Prepared');

  // 6. Multi-Agent Team Runtime
  const team = new TeamRuntime(agentRuntime);
  team.addMember('agent-alpha');
  team.addMember('agent-beta');
  team.startCollaboration();
  console.log('  -> Digital Team Formed and Ready');

  const t1 = performance.now();
  console.log(`[E2E] Bootstrap Completed in ${(t1 - t0).toFixed(2)}ms\n`);

  console.log('[E2E] Executing Demo Payload...');
  const exec0 = performance.now();

  // Execute Workflow
  const wfInstance = await scheduler.scheduleWorkflow(demoWf);
  if (wfInstance.getModel().state !== WorkflowState.Completed) {
    throw new Error('Workflow Execution Failed');
  }
  console.log('  -> Workflow Run Completed');

  // Assign Task to Team
  const assignee = team.delegate({
    taskId: 'e2e-task-1',
    payload: { act: 'review' },
    status: 'pending',
  });
  console.log(`  -> Task Delegated by Team Manager to: ${assignee}`);

  // Agent Runtime evaluates task
  const session = agentRuntime.createSession(assignee);
  await agentRuntime.invokeSkill(session.id, 'mock-skill-review');
  console.log('  -> Agent Resolved Task (Mock Skill) - state:', session.getContext().state);
  session.updateState(AgentState.Thinking);
  session.updateState(AgentState.Completed);

  team.complete();
  console.log('  -> Team Execution Completed');
  await host.shutdown();

  const exec1 = performance.now();
  console.log(`[E2E] Execution Completed in ${(exec1 - exec0).toFixed(2)}ms\n`);
  console.log('[E2E] ALL SYSTEMS NOMINAL');
}

bootstrap().catch(console.error);

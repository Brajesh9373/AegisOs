import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createTeam,
  delegateTask,
  sendMessage,
  teamStatus,
  hierarchyKeys,
  type TeamMemberSpec
} from '../api/hierarchy';

/** Live per-agent status; polls every `intervalMs` while runs are in flight. */
export function useTeamStatus(teamId: string | null, intervalMs = 3000) {
  return useQuery({
    queryKey: teamId ? hierarchyKeys.status(teamId) : ['hierarchy', 'status', 'none'],
    queryFn: () => teamStatus(teamId as string),
    enabled: teamId !== null,
    refetchInterval: intervalMs
  });
}

export function useCreateTeam() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (members?: TeamMemberSpec[]) => createTeam(members),
    onSuccess: team => {
      client.setQueryData(hierarchyKeys.team(team.team_id), team);
      void client.invalidateQueries({ queryKey: hierarchyKeys.teams });
    }
  });
}

export function useSendMessage(teamId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (args: { agentId: string; content: string }) =>
      sendMessage(teamId, args.agentId, args.content),
    onSettled: () => {
      void client.invalidateQueries({ queryKey: hierarchyKeys.status(teamId) });
      void client.invalidateQueries({ queryKey: hierarchyKeys.team(teamId) });
    }
  });
}

export function useDelegateTask(teamId: string) {
  return useMutation({
    mutationFn: (args: { fromAgent: string; toAgent: string; task: string }) =>
      delegateTask(teamId, args.fromAgent, args.toAgent, args.task)
  });
}

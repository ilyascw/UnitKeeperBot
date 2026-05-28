import { useMutation, useQueryClient, type UseMutationResult } from '@tanstack/react-query';

import { useAuthToken } from '@/auth/useAuth';

import {
  createGroup,
  joinGroup,
  leaveGroup,
  updateCurrentGroupSettings,
  updateCurrentGroupWeights,
} from './endpoints';
import { queryKeys } from './queries';
import type {
  CreateGroupRequest,
  CurrentContextResponse,
  GroupMembersResponse,
  GroupResponse,
  JoinGroupRequest,
  UpdateGroupSettingsRequest,
  UpdateWeightsRequest,
} from './types';

/**
 * Invalidate every query whose data could be affected by group membership or
 * settings changes. Centralised here so each mutation stays a one-liner.
 */
function useInvalidateGroup(): () => Promise<void> {
  const qc = useQueryClient();
  return async () => {
    await qc.invalidateQueries({ queryKey: queryKeys.currentGroup });
  };
}

export function useCreateGroup(): UseMutationResult<
  CurrentContextResponse,
  Error,
  CreateGroupRequest
> {
  const token = useAuthToken();
  const invalidate = useInvalidateGroup();
  return useMutation({
    mutationFn: (body: CreateGroupRequest) => createGroup(token, body),
    onSuccess: () => invalidate(),
  });
}

export function useJoinGroup(): UseMutationResult<
  CurrentContextResponse,
  Error,
  JoinGroupRequest
> {
  const token = useAuthToken();
  const invalidate = useInvalidateGroup();
  return useMutation({
    mutationFn: (body: JoinGroupRequest) => joinGroup(token, body),
    onSuccess: () => invalidate(),
  });
}

export function useLeaveGroup(): UseMutationResult<void, Error, void> {
  const token = useAuthToken();
  const invalidate = useInvalidateGroup();
  return useMutation({
    mutationFn: () => leaveGroup(token),
    onSuccess: () => invalidate(),
  });
}

export function useUpdateGroupSettings(): UseMutationResult<
  GroupResponse,
  Error,
  UpdateGroupSettingsRequest
> {
  const token = useAuthToken();
  const invalidate = useInvalidateGroup();
  return useMutation({
    mutationFn: (body: UpdateGroupSettingsRequest) => updateCurrentGroupSettings(token, body),
    onSuccess: () => invalidate(),
  });
}

export function useUpdateGroupWeights(): UseMutationResult<
  GroupMembersResponse,
  Error,
  UpdateWeightsRequest
> {
  const token = useAuthToken();
  const invalidate = useInvalidateGroup();
  return useMutation({
    mutationFn: (body: UpdateWeightsRequest) => updateCurrentGroupWeights(token, body),
    onSuccess: () => invalidate(),
  });
}

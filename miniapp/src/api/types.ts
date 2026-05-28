/**
 * TypeScript mirror of the backend API contract.
 *
 * Source of truth: `backend/src/unitkeeper_backend/api/schemas`.
 * Keep these in sync with the Pydantic schemas. Decimal values are serialised
 * as strings by the backend, so they are typed as `string` here.
 */

export interface UserResponse {
  id: number;
  username: string | null;
  first_name: string | null;
  last_name: string | null;
  language_code: string | null;
  is_bot: boolean;
}

export interface MembershipResponse {
  id: number;
  group_id: number;
  user_id: number;
  left_at: string | null;
  weight_percent: string | null;
}

export interface GroupResponse {
  id: number;
  name: string;
  owner_user_id: number;
  sprint_start_weekday: string;
  sprint_duration_days: number;
  timezone: string;
  balance: string;
  active_members: MembershipResponse[];
}

export interface CurrentContextResponse {
  user: UserResponse;
  membership: MembershipResponse | null;
  group: GroupResponse | null;
}

export interface SessionResponse {
  access_token: string;
  token_type: string;
  expires_at: string;
  context: CurrentContextResponse;
}

export interface MemberCardResponse {
  user_id: number;
  username: string | null;
  first_name: string | null;
  last_name: string | null;
  weight_percent: string;
  balance: string;
  is_owner: boolean;
}

export interface GroupCardResponse {
  id: number;
  name: string;
  owner_user_id: number;
  sprint_start_weekday: string;
  sprint_duration_days: number;
  timezone: string;
  group_balance: string;
  sprint_period_start: string;
  sprint_period_end: string;
  sprint_ends_at: string;
  members: MemberCardResponse[];
  join_secret: string | null;
}

/** Shape of the backend's structured error payload. */
export interface ErrorResponse {
  code: string;
  message: string;
}

export type Weekday =
  | 'monday'
  | 'tuesday'
  | 'wednesday'
  | 'thursday'
  | 'friday'
  | 'saturday'
  | 'sunday';

export const WEEKDAYS: readonly Weekday[] = [
  'monday',
  'tuesday',
  'wednesday',
  'thursday',
  'friday',
  'saturday',
  'sunday',
] as const;

export interface CreateGroupRequest {
  name: string;
  join_secret: string;
  sprint_start_weekday: Weekday;
  sprint_duration_days: number;
  timezone?: string;
}

export interface JoinGroupRequest {
  name: string;
  join_secret: string;
}

export interface UpdateGroupSettingsRequest {
  join_secret?: string;
  sprint_start_weekday?: Weekday;
  sprint_duration_days?: number;
}

export interface MemberWeightInput {
  user_id: number;
  weight_percent: string;
}

export interface UpdateWeightsRequest {
  weights: MemberWeightInput[];
}

export interface GroupMembersResponse {
  members: MemberCardResponse[];
}

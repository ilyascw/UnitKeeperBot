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
  details?: unknown;
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

/** A recurring task in the current group. Decimal `unit_cost` is a string. */
export interface TaskResponse {
  id: number;
  group_id: number;
  title: string;
  frequency_per_sprint: number;
  unit_cost: string;
  deleted_at: string | null;
  /** Confirmed completions in the current sprint. */
  completed_in_sprint: number;
  /** Slots left against the frequency cap (frequency − completed). */
  remaining_in_sprint: number;
  /** Completions logged but awaiting approval (holds). */
  pending_in_sprint: number;
  /** Slots still open to mark now: frequency − completed − pending. */
  available_in_sprint: number;
}

export interface CreateTaskRequest {
  title: string;
  frequency_per_sprint: number;
  unit_cost: string;
}

export interface UpdateTaskRequest {
  title?: string;
  frequency_per_sprint?: number;
  unit_cost?: string;
}

export interface BulkImportTaskItem {
  title: string;
  frequency_per_sprint: number;
  unit_cost: string;
}

export interface TaskImportRowError {
  index: number;
  field: string;
  message: string;
}

/** Result of marking a task done — a log entry pending owner approval. */
export interface TaskLogResponse {
  id: number;
  group_id: number;
  task_id: number;
  performer_user_id: number;
  status: string;
  approver_user_id: number | null;
  decided_at: string | null;
  rejection_reason: string | null;
  created_at: string;
}

export type TaskLogStatus = 'pending' | 'completed' | 'rejected';

export interface TaskLogTaskResponse {
  id: number;
  title: string;
  unit_cost: string;
  is_active: boolean;
}

export interface TaskLogViewResponse {
  id: number;
  group_id: number;
  task: TaskLogTaskResponse;
  status: TaskLogStatus;
  performer: UserResponse;
  approver: UserResponse | null;
  decided_at: string | null;
  rejection_reason: string | null;
  created_at: string;
}

export interface TaskLogPageResponse {
  items: TaskLogViewResponse[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface CompletedTaskBreakdownResponse {
  task_id: number;
  title: string;
  completed_count: number;
  completed_units: string;
}

export interface GroupProgressResponse {
  planned_units: string;
  completed_units: string;
  progress_percent: string;
}

/** Provisional results for the running sprint (before it is closed). */
export interface SprintResultsResponse {
  period_start: string;
  period_end: string;
  planned_units: string;
  completed_units: string;
  progress_percent: string;
  breakdown: CompletedTaskBreakdownResponse[];
  group: GroupProgressResponse;
}

export interface BalanceResponse {
  group_id: number;
  user_id: number;
  current_balance: string;
}

export interface TransferCandidateResponse {
  user: UserResponse;
  current_balance: string;
}

export interface TransferCandidatesResponse {
  candidates: TransferCandidateResponse[];
}

export interface CreateTransferRequest {
  recipient_user_id: number;
  amount: string;
}

export interface BalanceTransferResponse {
  group_id: number;
  sender_user_id: number;
  recipient_user_id: number;
  amount: string;
  sender_balance: string;
  recipient_balance: string;
}

export type BalanceTransactionType =
  | 'transfer'
  | 'sprint_settlement'
  | 'manual_adjustment';

export interface BalanceTransactionResponse {
  id: number;
  group_id: number;
  user_id: number;
  transaction_type: BalanceTransactionType | string;
  amount_delta: string;
  counterparty_user_id: number | null;
  description: string | null;
  created_at: string;
}

export interface BalanceTransactionPageResponse {
  items: BalanceTransactionResponse[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

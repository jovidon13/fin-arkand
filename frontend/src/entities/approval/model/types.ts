export const approvalStatuses = ["pending", "approved", "rejected"] as const;
export const voteValues = ["approve", "reject"] as const;

export type ApprovalStatus = (typeof approvalStatuses)[number];
export type VoteValueKind = (typeof voteValues)[number];

export interface ApprovalVote {
  id: number;
  owner: number;
  owner_name?: string | null;
  value: VoteValueKind;
  value_display?: string;
  comment: string;
  created_at?: string;
}

export interface ApprovalRequest {
  id: number;
  business: number;
  business_name?: string;
  amount: string;
  purpose: string;
  description: string;
  category: number | null;
  category_name?: string | null;
  status: ApprovalStatus;
  status_display: string;
  required_votes: number;
  approvals_count: number;
  rejections_count: number;
  occurred_on: string;
  requested_by?: number | null;
  requested_by_name?: string | null;
  decided_at?: string | null;
  votes?: ApprovalVote[];
  created_at?: string;
}

export interface CreateRequestPayload {
  business: number;
  amount: string;
  purpose: string;
  occurred_on: string;
  category?: number | null;
  description?: string;
}

export interface VotePayload {
  value: VoteValueKind;
  comment?: string;
}

export interface ApprovalFilters {
  business?: number;
  status?: string;
  category?: number;
  date_from?: string;
  date_to?: string;
  search?: string;
  ordering?: string;
  page?: number;
  page_size?: number;
}

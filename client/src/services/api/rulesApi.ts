import { api } from '@store/api/apiSlice';

// Rules API types
export interface Rule {
  id: number;
  state_code: string;
  legislation_source_id: number | null;
  legislation_digest_id: number | null;
  rule_text: string;
  applies_to_page_types: string | null;
  active: boolean;
  approved: boolean;
  is_manually_modified: boolean;
  original_rule_text: string | null;
  status: string;
  supersedes_rule_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface RuleCreate {
  state_code: string;
  legislation_source_id?: number;
  legislation_digest_id?: number;
  rule_text: string;
  applies_to_page_types?: string;
  active?: boolean;
  approved?: boolean;
  is_manually_modified?: boolean;
  original_rule_text?: string;
  status?: string;
  supersedes_rule_id?: number;
}

export interface RuleUpdate {
  state_code?: string;
  legislation_source_id?: number;
  legislation_digest_id?: number;
  rule_text?: string;
  applies_to_page_types?: string;
  active?: boolean;
  approved?: boolean;
  is_manually_modified?: boolean;
  original_rule_text?: string;
  status?: string;
  supersedes_rule_id?: number;
}

export interface RulesListParams {
  state_code?: string;
  active_only?: boolean;
  approved_only?: boolean;
}

export interface DigestLegislationParams {
  state_code: string;
  legislation_source_id?: number;
}

export const rulesApi = api.injectEndpoints({
  endpoints: (builder) => ({
    // Get all rules with optional filters
    getRules: builder.query<{ rules: Rule[]; total: number }, RulesListParams>({
      query: (params) => ({
        url: '/api/rules',
        params,
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.rules.map(({ id }) => ({ type: 'Rules' as const, id })),
              { type: 'Rules', id: 'LIST' },
            ]
          : [{ type: 'Rules', id: 'LIST' }],
    }),

    // Get single rule
    getRule: builder.query<Rule, number>({
      query: (id) => ({
        url: `/api/rules/${id}`,
      }),
      providesTags: (result, error, id) => [{ type: 'Rules', id }],
    }),

    // Create new rule
    createRule: builder.mutation<Rule, RuleCreate>({
      query: (data) => ({
        url: '/api/rules',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: [{ type: 'Rules', id: 'LIST' }],
    }),

    // Update rule
    updateRule: builder.mutation<Rule, { id: number; data: RuleUpdate }>({
      query: ({ id, data }) => ({
        url: `/api/rules/${id}`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'Rules', id },
        { type: 'Rules', id: 'LIST' },
      ],
    }),

    // Delete rule
    deleteRule: builder.mutation<void, number>({
      query: (id) => ({
        url: `/api/rules/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, id) => [
        { type: 'Rules', id },
        { type: 'Rules', id: 'LIST' },
      ],
    }),

    // Delete all rules for a state
    deleteStateRules: builder.mutation<{ deleted_count: number }, string>({
      query: (state_code) => ({
        url: `/api/rules/state/${state_code}`,
        method: 'DELETE',
      }),
      invalidatesTags: [{ type: 'Rules', id: 'LIST' }],
    }),

    // Digest legislation into rules
    digestLegislation: builder.mutation<
      { rules: Rule[]; message: string; deleted_count: number; created_count: number },
      number
    >({
      query: (source_id) => ({
        url: `/api/rules/legislation/${source_id}/digest`,
        method: 'POST',
      }),
      invalidatesTags: [{ type: 'Rules', id: 'LIST' }, 'States'],
    }),

    // Get rules for a specific legislation source
    getRulesByLegislation: builder.query<{ rules: Rule[]; total: number }, number>({
      query: (legislation_source_id) => ({
        url: `/api/rules/legislation/${legislation_source_id}`,
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.rules.map(({ id }) => ({ type: 'Rules' as const, id })),
              { type: 'Rules', id: 'LIST' },
            ]
          : [{ type: 'Rules', id: 'LIST' }],
    }),
  }),
});

export const {
  useGetRulesQuery,
  useGetRuleQuery,
  useCreateRuleMutation,
  useUpdateRuleMutation,
  useDeleteRuleMutation,
  useDeleteStateRulesMutation,
  useDigestLegislationMutation,
  useGetRulesByLegislationQuery,
} = rulesApi;

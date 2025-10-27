import { api } from '@store/api/apiSlice';

// States API
export interface State {
  id: number;
  code: string;
  name: string;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface StateCreate {
  code: string;
  name: string;
  active?: boolean;
}

export interface StateUpdate {
  name?: string;
  active?: boolean;
}

export interface LegislationSource {
  id: number;
  state_code: string;
  statute_number: string;
  title: string;
  full_text: string;
  source_url?: string;
  effective_date?: string;
  sunset_date?: string;
  last_verified_date?: string;
  applies_to_page_types?: string;
  created_at: string;
  updated_at: string;
}

export interface LegislationSourceCreate {
  state_code: string;
  statute_number: string;
  title: string;
  full_text: string;
  source_url?: string;
  effective_date?: string;
  sunset_date?: string;
  last_verified_date?: string;
  applies_to_page_types?: string;
}

export interface LegislationDigest {
  id: number;
  legislation_source_id: number;
  digest_type: 'universal' | 'page_specific';
  page_type_code?: string;
  interpreted_requirements: string;
  created_by?: number;
  reviewed_by?: number;
  last_review_date?: string;
  approved: boolean;
  created_at: string;
  updated_at: string;
}

export interface LegislationDigestCreate {
  legislation_source_id: number;
  digest_type: 'universal' | 'page_specific';
  page_type_code?: string;
  interpreted_requirements: string;
  created_by?: number;
}

export const statesApi = api.injectEndpoints({
  endpoints: (builder) => ({
    // States
    getStates: builder.query<{ states: State[]; total: number }, { active_only?: boolean }>({
      query: ({ active_only = false }) => ({
        url: '/api/states',
        params: { active_only },
      }),
      providesTags: ['States'],
    }),
    getState: builder.query<State, number>({
      query: (id) => ({
        url: `/api/states/${id}`,
      }),
      providesTags: (result, error, id) => [{ type: 'States', id }],
    }),
    getStateByCode: builder.query<State, string>({
      query: (code) => ({
        url: `/api/states/code/${code}`,
      }),
      providesTags: (result, error, code) => [{ type: 'States', id: code }],
    }),
    createState: builder.mutation<State, StateCreate>({
      query: (data) => ({
        url: '/api/states',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: (result) => [
        { type: 'States', id: result?.id },
        { type: 'States', id: result?.code },
        'States',
      ],
    }),
    updateState: builder.mutation<State, { id: number; data: StateUpdate }>({
      query: ({ id, data }) => ({
        url: `/api/states/${id}`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'States', id },
        { type: 'States', id: result?.code },
        'States',
      ],
    }),

    // Legislation Sources
    getLegislationSources: builder.query<
      { sources: LegislationSource[]; total: number },
      { state_code?: string }
    >({
      query: ({ state_code }) => ({
        url: '/api/states/legislation',
        params: state_code ? { state_code } : undefined,
      }),
      providesTags: ['LegislationSources'],
    }),
    getLegislationSource: builder.query<LegislationSource, number>({
      query: (id) => ({
        url: `/api/states/legislation/${id}`,
      }),
      providesTags: (result, error, id) => [{ type: 'LegislationSources', id }],
    }),
    createLegislationSource: builder.mutation<LegislationSource, LegislationSourceCreate>({
      query: (data) => ({
        url: '/api/states/legislation',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['LegislationSources'],
    }),
    updateLegislationSource: builder.mutation<
      LegislationSource,
      { id: number; data: Partial<LegislationSourceCreate> }
    >({
      query: ({ id, data }) => ({
        url: `/api/states/legislation/${id}`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'LegislationSources', id },
        'LegislationSources',
      ],
    }),
    deleteLegislationSource: builder.mutation<
      { message: string; legislation_source_id: number; statute_number: string; digests_deleted: number; rules_deleted: number },
      number
    >({
      query: (id) => ({
        url: `/api/states/legislation/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['LegislationSources', 'Rules'],
    }),

    // Legislation Digests
    getLegislationDigests: builder.query<
      { digests: LegislationDigest[]; total: number },
      { source_id: number; approved_only?: boolean }
    >({
      query: ({ source_id, approved_only = false }) => ({
        url: `/api/states/legislation/${source_id}/digests`,
        params: { approved_only },
      }),
      providesTags: ['LegislationDigests'],
    }),
    createLegislationDigest: builder.mutation<
      LegislationDigest,
      { source_id: number; data: LegislationDigestCreate }
    >({
      query: ({ source_id, data }) => ({
        url: `/api/states/legislation/${source_id}/digests`,
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['LegislationDigests'],
    }),
    updateLegislationDigest: builder.mutation<
      LegislationDigest,
      { id: number; data: { interpreted_requirements?: string; approved?: boolean; reviewed_by?: number } }
    >({
      query: ({ id, data }) => ({
        url: `/api/states/digests/${id}`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: 'LegislationDigests', id },
        'LegislationDigests',
      ],
    }),
  }),
});

export const {
  useGetStatesQuery,
  useGetStateQuery,
  useGetStateByCodeQuery,
  useCreateStateMutation,
  useUpdateStateMutation,
  useGetLegislationSourcesQuery,
  useGetLegislationSourceQuery,
  useCreateLegislationSourceMutation,
  useUpdateLegislationSourceMutation,
  useDeleteLegislationSourceMutation,
  useGetLegislationDigestsQuery,
  useCreateLegislationDigestMutation,
  useUpdateLegislationDigestMutation,
} = statesApi;

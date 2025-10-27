import { api } from '@store/api/apiSlice';

export interface PreambleTemplate {
  id: number;
  name: string;
  description?: string;
  template_structure: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface Preamble {
  id: number;
  name: string;
  machine_name: string;
  scope: 'universal' | 'state' | 'page_type' | 'project';
  page_type_code?: string;
  state_code?: string;
  project_id?: number;
  created_via: 'config' | 'project_override';
  created_at: string;
  created_by?: number;
  active_version?: PreambleVersion;
}

export interface PreambleCreate {
  name: string;
  scope: 'universal' | 'state' | 'page_type' | 'project';
  page_type_code?: string;
  state_code?: string;
  project_id?: number;
  created_via: 'config' | 'project_override';
  created_by?: number;
  initial_text: string;
}

export interface PreambleVersion {
  id: number;
  preamble_id: number;
  version_number: number;
  preamble_text: string;
  change_summary?: string;
  status: 'draft' | 'active' | 'retired';
  created_at: string;
  created_by?: number;
  performance?: PreambleVersionPerformance;
}

export interface PreambleVersionCreate {
  preamble_id: number;
  preamble_text: string;
  change_summary?: string;
  created_by?: number;
}

export interface PreambleVersionPerformance {
  id: number;
  preamble_version_id: number;
  test_runs_count: number;
  avg_score?: number;
  score_stddev?: number;
  avg_confidence?: number;
  false_positive_rate?: number;
  false_negative_rate?: number;
  avg_cost?: number;
  avg_duration_seconds?: number;
  last_tested_at?: string;
}

export interface PreambleTestRun {
  id: number;
  preamble_version_id: number;
  url_id: number;
  run_date: string;
  score_achieved?: number;
  violations_found?: string;
  confidence_score?: number;
  token_count?: number;
  cost?: number;
  duration_seconds?: number;
  model_used: string;
  false_positive?: boolean;
  false_negative?: boolean;
}

export interface PreambleTestRunCreate {
  preamble_version_id: number;
  url_id: number;
  score_achieved?: number;
  violations_found?: string;
  confidence_score?: number;
  token_count?: number;
  cost?: number;
  duration_seconds?: number;
  model_used: string;
  false_positive?: boolean;
  false_negative?: boolean;
}

export const preamblesApi = api.injectEndpoints({
  endpoints: (builder) => ({
    // Templates
    getPreambleTemplates: builder.query<{ templates: PreambleTemplate[]; total: number }, void>({
      query: () => '/preambles/templates',
      providesTags: ['PreambleTemplates'],
    }),
    getPreambleTemplate: builder.query<PreambleTemplate, number>({
      query: (id) => `/preambles/templates/${id}`,
      providesTags: (result, error, id) => [{ type: 'PreambleTemplates', id }],
    }),
    createPreambleTemplate: builder.mutation<PreambleTemplate, Omit<PreambleTemplate, 'id' | 'created_at' | 'updated_at'>>({
      query: (data) => ({
        url: '/api/preambles/templates',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['PreambleTemplates'],
    }),

    // Preambles
    getPreambles: builder.query<
      { preambles: Preamble[]; total: number },
      { scope?: string; state_code?: string; page_type_code?: string; project_id?: number }
    >({
      query: (params) => ({
        url: '/api/preambles',
        params,
      }),
      providesTags: ['Preambles'],
    }),
    getPreamble: builder.query<Preamble, number>({
      query: (id) => `/preambles/${id}`,
      providesTags: (result, error, id) => [{ type: 'Preambles', id }],
    }),
    createPreamble: builder.mutation<Preamble, PreambleCreate>({
      query: (data) => ({
        url: '/api/preambles',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['Preambles'],
    }),

    // Versions
    getPreambleVersions: builder.query<{ versions: PreambleVersion[]; total: number }, number>({
      query: (preambleId) => `/preambles/${preambleId}/versions`,
      providesTags: ['PreambleVersions'],
    }),
    getPreambleVersion: builder.query<PreambleVersion, number>({
      query: (id) => `/preambles/versions/${id}`,
      providesTags: (result, error, id) => [{ type: 'PreambleVersions', id }],
    }),
    createPreambleVersion: builder.mutation<
      PreambleVersion,
      { preambleId: number; data: PreambleVersionCreate }
    >({
      query: ({ preambleId, data }) => ({
        url: `/preambles/${preambleId}/versions`,
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['PreambleVersions', 'Preambles'],
    }),
    activatePreambleVersion: builder.mutation<PreambleVersion, number>({
      query: (versionId) => ({
        url: `/preambles/versions/${versionId}/activate`,
        method: 'PATCH',
      }),
      invalidatesTags: ['PreambleVersions', 'Preambles'],
    }),

    // Test Runs
    getPreambleTestRuns: builder.query<
      { test_runs: PreambleTestRun[]; total: number },
      { preamble_version_id?: number }
    >({
      query: (params) => ({
        url: '/api/preambles/test-runs',
        params,
      }),
      providesTags: ['PreambleTestRuns'],
    }),
    createPreambleTestRun: builder.mutation<PreambleTestRun, PreambleTestRunCreate>({
      query: (data) => ({
        url: '/api/preambles/test-runs',
        method: 'POST',
        body: data,
      }),
      invalidatesTags: ['PreambleTestRuns', 'PreambleVersions'],
    }),

    // Performance
    getPreambleVersionPerformance: builder.query<PreambleVersionPerformance, number>({
      query: (versionId) => `/preambles/versions/${versionId}/performance`,
      providesTags: (result, error, id) => [{ type: 'PreambleVersions', id }],
    }),

    // Composition
    composePreamble: builder.mutation<
      { composed_text: string; cached: boolean; components: Record<string, any> },
      { project_id: number; page_type_code: string; state_code?: string }
    >({
      query: (data) => ({
        url: '/api/preambles/compose',
        method: 'POST',
        body: data,
      }),
    }),
  }),
});

export const {
  useGetPreambleTemplatesQuery,
  useGetPreambleTemplateQuery,
  useCreatePreambleTemplateMutation,
  useGetPreamblesQuery,
  useGetPreambleQuery,
  useCreatePreambleMutation,
  useGetPreambleVersionsQuery,
  useGetPreambleVersionQuery,
  useCreatePreambleVersionMutation,
  useActivatePreambleVersionMutation,
  useGetPreambleTestRunsQuery,
  useCreatePreambleTestRunMutation,
  useGetPreambleVersionPerformanceQuery,
  useComposePreambleMutation,
} = preamblesApi;

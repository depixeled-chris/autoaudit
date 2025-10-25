import { createApi } from '@reduxjs/toolkit/query/react';
import type { AxiosRequestConfig } from 'axios';
import apiClient from '@lib/api/axios';

// Axios base query for RTK Query
const axiosBaseQuery =
  () =>
  async ({ url, method = 'GET', data, params }: AxiosRequestConfig & { url: string }) => {
    try {
      const result = await apiClient({
        url,
        method,
        data,
        params,
      });
      return { data: result.data };
    } catch (axiosError: any) {
      const err = axiosError;
      return {
        error: {
          status: err.response?.status,
          data: err.response?.data || err.message,
        },
      };
    }
  };

// Define types
export interface Project {
  id: number;
  name: string;
  description: string | null;
  state_code: string;
  base_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  state_code: string;
  description?: string;
  base_url?: string;
}

export interface ProjectSummary {
  total_urls: number;
  total_checks: number;
  avg_score: number;
  compliant_count: number;
  total_violations: number;
}

export interface URL {
  id: number;
  project_id: number | null;
  url: string;
  url_type: string;
  template_id: string | null;
  platform: string | null;
  active: boolean;
  check_frequency_hours: number;
  last_checked: string | null;
  created_at: string;
}

export interface URLCreate {
  url: string;
  project_id?: number;
  url_type?: string;
  template_id?: string;
  platform?: string;
  check_frequency_hours?: number;
}

export interface Check {
  id: number;
  url_id: number;
  url: string;
  state_code: string;
  template_id: string | null;
  overall_score: number | null;
  compliance_status: string | null;
  summary: string | null;
  checked_at: string;
  violations?: Violation[];
  visual_verifications?: VisualVerification[];
}

export interface Violation {
  id: number;
  check_id: number;
  category: string;
  severity: string;
  rule_violated: string;
  rule_key: string | null;
  confidence: number | null;
  explanation: string | null;
  evidence: string | null;
}

export interface VisualVerification {
  id: number;
  check_id: number;
  rule_key: string;
  rule_text: string | null;
  is_compliant: boolean;
  confidence: number;
  verification_method: string;
  visual_evidence: string | null;
  cached: boolean;
}

// Create API slice
export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: axiosBaseQuery(),
  tagTypes: ['Project', 'URL', 'Check'],
  endpoints: (builder) => ({
    // Projects
    getProjects: builder.query<Project[], void>({
      query: () => ({ url: '/api/projects' }),
      providesTags: ['Project'],
    }),
    getProject: builder.query<Project, number>({
      query: (id) => ({ url: `/api/projects/${id}` }),
      providesTags: (_result, _error, id) => [{ type: 'Project', id }],
    }),
    createProject: builder.mutation<Project, ProjectCreate>({
      query: (data) => ({
        url: '/api/projects',
        method: 'POST',
        data,
      }),
      invalidatesTags: ['Project'],
    }),
    getProjectSummary: builder.query<ProjectSummary, number>({
      query: (id) => ({ url: `/api/projects/${id}/summary` }),
    }),

    // URLs
    getURLs: builder.query<URL[], { project_id?: number; active_only?: boolean }>({
      query: (params) => ({
        url: '/api/urls',
        params,
      }),
      providesTags: ['URL'],
    }),
    getURL: builder.query<URL, number>({
      query: (id) => ({ url: `/api/urls/${id}` }),
      providesTags: (_result, _error, id) => [{ type: 'URL', id }],
    }),
    createURL: builder.mutation<URL, URLCreate>({
      query: (data) => ({
        url: '/api/urls',
        method: 'POST',
        data,
      }),
      invalidatesTags: ['URL'],
    }),

    // Checks
    getChecks: builder.query<
      Check[],
      { url_id?: number; state_code?: string; limit?: number }
    >({
      query: (params) => ({
        url: '/api/checks',
        params,
      }),
      providesTags: ['Check'],
    }),
    getCheck: builder.query<Check, { id: number; include_details?: boolean }>({
      query: ({ id, include_details = true }) => ({
        url: `/api/checks/${id}`,
        params: { include_details },
      }),
      providesTags: (_result, _error, { id }) => [{ type: 'Check', id }],
    }),
    runCheck: builder.mutation<
      Check,
      { url: string; state_code: string; project_id?: number }
    >({
      query: (data) => ({
        url: '/api/checks',
        method: 'POST',
        data,
      }),
      invalidatesTags: ['Check'],
    }),
    getCheckViolations: builder.query<Violation[], number>({
      query: (id) => ({ url: `/api/checks/${id}/violations` }),
    }),
  }),
});

export const {
  useGetProjectsQuery,
  useGetProjectQuery,
  useCreateProjectMutation,
  useGetProjectSummaryQuery,
  useGetURLsQuery,
  useGetURLQuery,
  useCreateURLMutation,
  useGetChecksQuery,
  useGetCheckQuery,
  useRunCheckMutation,
  useGetCheckViolationsQuery,
} = apiSlice;

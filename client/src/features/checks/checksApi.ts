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

// Check types
export interface Violation {
  id: number;
  check_id: number;
  category: string;
  severity: string;
  rule_violated: string;
  rule_key: string | null;
  confidence: number | null;
  needs_visual_verification: boolean;
  explanation: string | null;
  evidence: string | null;
  created_at: string;
}

export interface VisualVerification {
  id: number;
  check_id: number;
  rule_key: string;
  rule_text: string;
  is_compliant: boolean;
  confidence: number;
  verification_method: string;
  visual_evidence: string | null;
  proximity_description: string | null;
  screenshot_path: string | null;
  cached: boolean;
  created_at: string;
}

export interface Check {
  id: number;
  url_id: number;
  url: string;
  state_code: string;
  template_id: string | null;
  overall_score: number;
  compliance_status: string;
  summary: string;
  llm_input_path: string | null;
  llm_input_text: string | null;
  report_path: string | null;
  checked_at: string;
  violations?: Violation[];
  visual_verifications?: VisualVerification[];
}

// Create Checks API slice
export const checksApi = createApi({
  reducerPath: 'checksApi',
  baseQuery: axiosBaseQuery(),
  tagTypes: ['Check'],
  endpoints: (builder) => ({
    getCheck: builder.query<Check, number>({
      query: (checkId) => ({
        url: `/api/checks/${checkId}`,
        params: { include_details: true },
      }),
      providesTags: (_result, _error, checkId) => [{ type: 'Check', id: checkId }],
    }),
    listChecks: builder.query<Check[], { url_id?: number; state_code?: string; limit?: number }>({
      query: ({ url_id, state_code, limit = 100 }) => ({
        url: '/api/checks',
        params: { url_id, state_code, limit },
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.map(({ id }) => ({ type: 'Check' as const, id })),
              { type: 'Check', id: 'LIST' },
            ]
          : [{ type: 'Check', id: 'LIST' }],
    }),
    getLatestCheckForUrl: builder.query<Check | null, number>({
      query: (urlId) => ({
        url: `/api/checks`,
        params: { url_id: urlId, limit: 1, include_details: true },
      }),
      transformResponse: (response: Check[]) => {
        return response.length > 0 ? response[0] : null;
      },
      providesTags: (_result, _error, urlId) => [{ type: 'Check', id: `url-${urlId}` }],
    }),
  }),
});

export const {
  useGetCheckQuery,
  useListChecksQuery,
  useGetLatestCheckForUrlQuery,
} = checksApi;

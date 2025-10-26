import { createApi } from '@reduxjs/toolkit/query/react';
import type { AxiosRequestConfig } from 'axios';
import apiClient from '@lib/api/axios';
import { checksApi } from '@features/checks/checksApi';

// Axios base query for RTK Query
const axiosBaseQuery =
  () =>
  async ({ url, method = 'GET', data, params, timeout }: AxiosRequestConfig & { url: string }) => {
    try {
      const result = await apiClient({
        url,
        method,
        data,
        params,
        timeout, // Allow custom timeout per request
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

// URL types (renamed from URL to MonitoredURL to avoid conflict with native URL class)
export interface MonitoredURL {
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
  check_count: number;
}

export interface URLCreate {
  url: string;
  project_id?: number;
  url_type?: string;
  template_id?: string;
  platform?: string;
  check_frequency_hours?: number;
}

export interface URLUpdate {
  active?: boolean;
  check_frequency_hours?: number;
  template_id?: string;
}

// Create URLs API slice
export const urlsApi = createApi({
  reducerPath: 'urlsApi',
  baseQuery: axiosBaseQuery(),
  tagTypes: ['URL'],
  endpoints: (builder) => ({
    getURLs: builder.query<MonitoredURL[], { project_id?: number; active_only?: boolean }>({
      query: ({ project_id, active_only = true }) => ({
        url: '/api/urls',
        params: { project_id, active_only },
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.map(({ id }) => ({ type: 'URL' as const, id })),
              { type: 'URL', id: 'LIST' },
            ]
          : [{ type: 'URL', id: 'LIST' }],
    }),
    getURL: builder.query<MonitoredURL, number>({
      query: (id) => ({ url: `/api/urls/${id}` }),
      providesTags: (_result, _error, id) => [{ type: 'URL', id }],
    }),
    createURL: builder.mutation<MonitoredURL, URLCreate>({
      query: (data) => ({
        url: '/api/urls',
        method: 'POST',
        data,
      }),
      invalidatesTags: [{ type: 'URL', id: 'LIST' }],
    }),
    updateURL: builder.mutation<MonitoredURL, { id: number; data: URLUpdate }>({
      query: ({ id, data }) => ({
        url: `/api/urls/${id}`,
        method: 'PATCH',
        data,
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: 'URL', id },
        { type: 'URL', id: 'LIST' },
      ],
    }),
    deleteURL: builder.mutation<void, number>({
      query: (id) => ({
        url: `/api/urls/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: [{ type: 'URL', id: 'LIST' }],
    }),
    forceRescanURL: builder.mutation<void, number>({
      query: (id) => ({
        url: `/api/urls/${id}/rescan`,
        method: 'POST',
        timeout: 120000, // 2 minutes - scans can take 30-60 seconds
      }),
      invalidatesTags: (_result, _error, id) => [
        { type: 'URL', id },
        { type: 'URL', id: 'LIST' },
      ],
      // After successful rescan, invalidate check queries for this URL
      async onQueryStarted(id, { dispatch, queryFulfilled }) {
        try {
          await queryFulfilled;
          // Invalidate the check data for this URL so modal auto-refreshes
          dispatch(checksApi.util.invalidateTags([{ type: 'Check', id: `url-${id}` }]));
        } catch {
          // Ignore errors
        }
      },
    }),
  }),
});

export const {
  useGetURLsQuery,
  useGetURLQuery,
  useCreateURLMutation,
  useUpdateURLMutation,
  useDeleteURLMutation,
  useForceRescanURLMutation,
} = urlsApi;

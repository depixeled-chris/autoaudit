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

// Page Type interfaces
export interface PageType {
  id: number;
  code: string;
  name: string;
  description: string | null;
  active: boolean;
  preamble: string | null;
  extraction_template: string | null;
  requires_llm_visual_confirmation: boolean;
  requires_human_confirmation: boolean;
  created_at: string;
  updated_at: string;
}

export interface PageTypeCreate {
  code: string;
  name: string;
  description?: string;
}

export interface PageTypeUpdate {
  name?: string;
  description?: string;
  active?: boolean;
  preamble?: string;
  extraction_template?: string;
  requires_llm_visual_confirmation?: boolean;
  requires_human_confirmation?: boolean;
}

// Create Page Types API slice
export const pageTypesApi = createApi({
  reducerPath: 'pageTypesApi',
  baseQuery: axiosBaseQuery(),
  tagTypes: ['PageType'],
  endpoints: (builder) => ({
    getPageTypes: builder.query<PageType[], { activeOnly?: boolean }>({
      query: ({ activeOnly = false }) => ({
        url: '/api/page-types',
        params: { active_only: activeOnly },
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.map(({ id }) => ({ type: 'PageType' as const, id })),
              { type: 'PageType', id: 'LIST' },
            ]
          : [{ type: 'PageType', id: 'LIST' }],
    }),
    getPageType: builder.query<PageType, number>({
      query: (id) => ({ url: `/api/page-types/${id}` }),
      providesTags: (_result, _error, id) => [{ type: 'PageType', id }],
    }),
    createPageType: builder.mutation<PageType, PageTypeCreate>({
      query: (data) => ({
        url: '/api/page-types',
        method: 'POST',
        data,
      }),
      invalidatesTags: [{ type: 'PageType', id: 'LIST' }],
    }),
    updatePageType: builder.mutation<PageType, { id: number; data: PageTypeUpdate }>({
      query: ({ id, data }) => ({
        url: `/api/page-types/${id}`,
        method: 'PATCH',
        data,
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: 'PageType', id },
        { type: 'PageType', id: 'LIST' },
      ],
    }),
    deletePageType: builder.mutation<void, number>({
      query: (id) => ({
        url: `/api/page-types/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: [{ type: 'PageType', id: 'LIST' }],
    }),
  }),
});

export const {
  useGetPageTypesQuery,
  useGetPageTypeQuery,
  useCreatePageTypeMutation,
  useUpdatePageTypeMutation,
  useDeletePageTypeMutation,
} = pageTypesApi;

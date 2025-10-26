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

// Project types
export interface Project {
  id: number;
  name: string;
  description: string | null;
  state_code: string;
  base_url: string | null;
  screenshot_path: string | null;
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
  project_id: number;
  project_name: string;
  total_urls: number;
  total_checks: number;
  avg_score: number;
  compliant_count: number;
  total_violations: number;
  total_text_tokens: number;
  total_visual_tokens: number;
  total_tokens: number;
}

// Create Projects API slice
export const projectsApi = createApi({
  reducerPath: 'projectsApi',
  baseQuery: axiosBaseQuery(),
  tagTypes: ['Project'],
  endpoints: (builder) => ({
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
    captureProjectScreenshot: builder.mutation<Project, number>({
      query: (id) => ({
        url: `/api/projects/${id}/screenshot`,
        method: 'POST',
      }),
      invalidatesTags: (_result, _error, id) => [{ type: 'Project', id }],
    }),
    deleteProject: builder.mutation<void, number>({
      query: (id) => ({
        url: `/api/projects/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Project'],
    }),
  }),
});

export const {
  useGetProjectsQuery,
  useGetProjectQuery,
  useCreateProjectMutation,
  useGetProjectSummaryQuery,
  useCaptureProjectScreenshotMutation,
  useDeleteProjectMutation,
} = projectsApi;

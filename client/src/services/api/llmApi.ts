import { apiSlice } from '../../store/api/apiSlice';

export interface LLMLog {
  id: number;
  api_endpoint: string;
  operation_type: string;
  user_id: number | null;
  model: string;
  provider: string;
  input_text: string;
  output_text: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  input_cost_usd: number | null;
  output_cost_usd: number | null;
  total_cost_usd: number | null;
  duration_ms: number | null;
  status: string;
  error_message: string | null;
  request_id: string | null;
  related_entity_type: string | null;
  related_entity_id: number | null;
  created_at: string;
}

export interface LLMLogsResponse {
  logs: LLMLog[];
  total: number;
  total_cost_usd: number;
}

export interface LLMStats {
  total_calls: number;
  total_tokens: number;
  total_cost_usd: number;
  avg_duration_ms: number;
  by_operation: Array<{
    operation_type: string;
    calls: number;
    tokens: number;
    cost_usd: number;
  }>;
  by_model: Array<{
    model: string;
    calls: number;
    tokens: number;
    cost_usd: number;
  }>;
  by_status: Array<{
    status: string;
    calls: number;
  }>;
}

export interface ModelConfig {
  id: number;
  operation_type: string;
  model: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface ModelConfigsResponse {
  configs: ModelConfig[];
  total: number;
}

export const llmApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    // LLM Logs
    getLLMLogs: builder.query<LLMLogsResponse, {
      limit?: number;
      offset?: number;
      operation_type?: string;
      model?: string;
      status?: string;
    }>({
      query: (params) => ({
        url: '/api/llm/logs',
        params,
      }),
      providesTags: ['LLMLogs'],
    }),

    getLLMLog: builder.query<LLMLog, number>({
      query: (id) => ({ url: `/api/llm/logs/${id}` }),
      providesTags: (result, error, id) => [{ type: 'LLMLogs', id }],
    }),

    getLLMStats: builder.query<LLMStats, void>({
      query: () => ({ url: '/api/llm/stats' }),
      providesTags: ['LLMStats'],
    }),

    // Available Models
    getAvailableModels: builder.query<string[], void>({
      query: () => ({ url: '/api/llm/models/available' }),
    }),

    // Model Configuration
    getModelConfigs: builder.query<ModelConfigsResponse, void>({
      query: () => ({ url: '/api/llm/models' }),
      providesTags: ['ModelConfigs'],
    }),

    updateModelConfig: builder.mutation<ModelConfig, {
      operation_type: string;
      model: string;
    }>({
      query: ({ operation_type, model }) => ({
        url: `/api/llm/models/${operation_type}`,
        method: 'PATCH',
        body: { model },
      }),
      invalidatesTags: ['ModelConfigs'],
    }),
  }),
});

export const {
  useGetLLMLogsQuery,
  useGetLLMLogQuery,
  useGetLLMStatsQuery,
  useGetAvailableModelsQuery,
  useGetModelConfigsQuery,
  useUpdateModelConfigMutation,
} = llmApi;

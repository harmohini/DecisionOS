import axios from 'axios';
import { SystemHealth, FullResearchResponse } from '../types';

const API_BASE_URL = 
  import.meta.env.VITE_API_BASE_URL || 
  import.meta.env.VITE_API_URL || 
  'http://127.0.0.1:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60s timeout for complete multi-agent research pipeline
});

export const checkHealth = async (): Promise<SystemHealth> => {
  try {
    const response = await apiClient.get<SystemHealth>('/api/v1/health');
    return response.data;
  } catch (error: any) {
    try {
      const fallbackResponse = await apiClient.get<SystemHealth>('/health');
      return fallbackResponse.data;
    } catch (err: any) {
      console.error(`[DecisionOS API Error] Health check failed for ${API_BASE_URL}`, {
        status: err.response?.status || error.response?.status,
        message: err.message,
      });
      throw err;
    }
  }
};

export const submitDecisionResearch = async (query: string): Promise<FullResearchResponse> => {
  const endpoint = '/api/v1/decisions/research';
  try {
    const response = await apiClient.post<FullResearchResponse>(endpoint, {
      query,
    });
    return response.data;
  } catch (error: any) {
    const status = error.response?.status;
    const detail = error.response?.data?.detail || error.message;
    console.error(`[DecisionOS API Error] POST ${endpoint} failed`, {
      status,
      detail,
    });
    if (detail) {
      throw new Error(`[HTTP ${status || 'Error'}] ${detail}`);
    }
    throw new Error(`[Network Error] Could not connect to DecisionOS backend at ${API_BASE_URL}`);
  }
};


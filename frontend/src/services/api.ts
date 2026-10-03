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
      // Alt fallback: try localhost:8000 if 127.0.0.1 fails due to browser hostname resolution
      try {
        const altResponse = await axios.get<SystemHealth>('http://localhost:8000/api/v1/health', { timeout: 5000 });
        return altResponse.data;
      } catch (altErr: any) {
        console.error(`[DecisionOS API Error] Health check failed for ${API_BASE_URL}`, {
          status: altErr.response?.status || error.response?.status,
          message: altErr.message,
        });
        throw altErr;
      }
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
    // Alt fallback: try localhost:8000 if 127.0.0.1 target fails
    try {
      const altResponse = await axios.post<FullResearchResponse>(`http://localhost:8000${endpoint}`, { query }, { timeout: 60000 });
      return altResponse.data;
    } catch (altErr: any) {
      const status = altErr.response?.status || error.response?.status;
      const detail = altErr.response?.data?.detail || error.response?.data?.detail || altErr.message;
      console.error(`[DecisionOS API Error] POST ${endpoint} failed`, {
        status,
        detail,
      });
      if (detail) {
        throw new Error(`[HTTP ${status || 'Error'}] ${detail}`);
      }
      throw new Error(`[Network Error] Could not connect to DecisionOS backend at ${API_BASE_URL} or http://localhost:8000`);
    }
  }
};

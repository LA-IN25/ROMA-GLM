import axios, { AxiosInstance, AxiosResponse } from 'axios';
import toast from 'react-hot-toast';
import {
  SolveRequest,
  Execution,
  ExecutionList,
  Health,
  Metrics,
  StatusPolling,
  Checkpoint,
  CheckpointList,
  TaskTrace,
  LMTrace,
  ExecutionData,
  ErrorResponse,
  AgentProfile,
  ConfigUpdateRequest,
} from '@/types/api';

class ApiClient {
  private client: AxiosInstance;

  constructor(baseURL: string = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add any auth headers here if needed
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      (error) => {
        const handleError = (error: any) => {
          const message = error.response?.data?.detail || error.message || 'An error occurred';
          
          if (error.response?.status === 401) {
            toast.error('Authentication required');
          } else if (error.response?.status === 403) {
            toast.error('Access forbidden');
          } else if (error.response?.status === 404) {
            toast.error('Resource not found');
          } else if (error.response?.status >= 500) {
            toast.error('Server error. Please try again later.');
          } else {
            toast.error(message);
          }
          
          return Promise.reject(error);
        };

        return handleError(error);
      }
    );
  }

  // Health endpoints
  async getHealth(): Promise<Health> {
    const response = await this.client.get<Health>('/health');
    return response.data;
  }

  // Execution endpoints
  async createExecution(request: SolveRequest): Promise<Execution> {
    const response = await this.client.post<Execution>('/api/v1/executions', request);
    toast.success('Execution started successfully');
    return response.data;
  }

  async getExecutions(offset: number = 0, limit: number = 20): Promise<ExecutionList> {
    const response = await this.client.get<ExecutionList>('/api/v1/executions', {
      params: { offset, limit },
    });
    return response.data;
  }

  async getExecution(executionId: string): Promise<Execution> {
    const response = await this.client.get<Execution>(`/api/v1/executions/${executionId}`);
    return response.data;
  }

  async getExecutionStatus(executionId: string): Promise<StatusPolling> {
    const response = await this.client.get<StatusPolling>(`/api/v1/executions/${executionId}/status`);
    return response.data;
  }

  async getExecutionMetrics(executionId: string): Promise<Metrics> {
    const response = await this.client.get<Metrics>(`/api/v1/executions/${executionId}/metrics`);
    return response.data;
  }

  async getExecutionData(executionId: string): Promise<ExecutionData> {
    const response = await this.client.get<ExecutionData>(`/api/v1/executions/${executionId}/data`);
    return response.data;
  }

  async deleteExecution(executionId: string): Promise<void> {
    await this.client.delete(`/api/v1/executions/${executionId}`);
    toast.success('Execution deleted successfully');
  }

  // Checkpoint endpoints
  async getCheckpoints(executionId: string): Promise<CheckpointList> {
    const response = await this.client.get<CheckpointList>(`/api/v1/checkpoints`, {
      params: { execution_id: executionId },
    });
    return response.data;
  }

  async getCheckpoint(checkpointId: string): Promise<Checkpoint> {
    const response = await this.client.get<Checkpoint>(`/api/v1/checkpoints/${checkpointId}`);
    return response.data;
  }

  async restoreCheckpoint(checkpointId: string, resume: boolean = true): Promise<void> {
    await this.client.post(`/api/v1/checkpoints/${checkpointId}/restore`, { resume });
    toast.success('Checkpoint restored successfully');
  }

  // Trace endpoints
  async getTaskTraces(executionId: string): Promise<TaskTrace[]> {
    const response = await this.client.get<TaskTrace[]>(`/api/v1/traces/tasks`, {
      params: { execution_id: executionId },
    });
    return response.data;
  }

  async getLMTraces(executionId: string): Promise<LMTrace[]> {
    const response = await this.client.get<LMTrace[]>(`/api/v1/traces/lm`, {
      params: { execution_id: executionId },
    });
    return response.data;
  }

  // Configuration endpoints
  async updateConfig(request: ConfigUpdateRequest): Promise<void> {
    await this.client.post('/api/v1/config/update', request);
    toast.success('Configuration updated successfully');
  }

  async getProfiles(): Promise<AgentProfile[]> {
    // This would need to be implemented on the backend
    // For now, return mock data
    const response = await this.client.get<AgentProfile[]>('/api/v1/config/profiles');
    return response.data;
  }

  async getProfile(profileName: string): Promise<AgentProfile> {
    const response = await this.client.get<AgentProfile>(`/api/v1/config/profiles/${profileName}`);
    return response.data;
  }

  // Utility methods
  async pollExecutionStatus(
    executionId: string,
    onUpdate: (status: StatusPolling) => void,
    interval: number = 2000
  ): Promise<() => void> {
    const poll = async () => {
      try {
        const status = await this.getExecutionStatus(executionId);
        onUpdate(status);
        
        // Stop polling if execution is complete
        if (['completed', 'failed', 'cancelled'].includes(status.status)) {
          return;
        }
        
        setTimeout(poll, interval);
      } catch (error) {
        console.error('Error polling execution status:', error);
      }
    };

    poll();

    // Return a function to stop polling
    return () => {
      // In a real implementation, you'd want to track the timeout ID
      // and clear it here
    };
  }

  // WebSocket connection for real-time updates (placeholder)
  connectWebSocket(executionId: string): WebSocket {
    const wsUrl = `${this.client.defaults.baseURL?.replace('http', 'ws')}/ws/executions/${executionId}`;
    return new WebSocket(wsUrl);
  }
}

// Create singleton instance
export const apiClient = new ApiClient();

// Export individual methods for convenience
export const {
  getHealth,
  createExecution,
  getExecutions,
  getExecution,
  getExecutionStatus,
  getExecutionMetrics,
  getExecutionData,
  deleteExecution,
  getCheckpoints,
  getCheckpoint,
  restoreCheckpoint,
  getTaskTraces,
  getLMTraces,
  updateConfig,
  getProfiles,
  getProfile,
  pollExecutionStatus,
  connectWebSocket,
} = apiClient;

export default apiClient;
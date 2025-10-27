// API Types based on ROMA-DSPy backend schemas

export interface SolveRequest {
  goal: string;
  max_depth?: number;
  config_profile?: string;
  config_overrides?: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface TaskNode {
  task_id: string;
  goal: string;
  status: string;
  depth: number;
  node_type?: string;
  parent_id?: string;
  result?: any;
  error?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface DAGStatistics {
  dag_id: string;
  total_tasks: number;
  status_counts: Record<string, number>;
  depth_distribution: Record<number, number>;
  num_subgraphs: number;
  is_complete: boolean;
}

export interface Execution {
  execution_id: string;
  status: string;
  initial_goal: string;
  max_depth: number;
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  created_at: string;
  updated_at: string;
  config?: Record<string, any>;
  metadata: Record<string, any>;
  statistics?: DAGStatistics;
}

export interface ExecutionList {
  executions: Execution[];
  total: number;
  offset: number;
  limit: number;
}

export interface Checkpoint {
  checkpoint_id: string;
  execution_id: string;
  created_at: string;
  trigger: string;
  state: string;
  file_path?: string;
  file_size_bytes?: number;
  compressed: boolean;
  dag_snapshot?: Record<string, any>;
}

export interface CheckpointList {
  checkpoints: Checkpoint[];
  total: number;
}

export interface TaskTrace {
  trace_id: number;
  execution_id: string;
  task_id: string;
  parent_task_id?: string;
  created_at: string;
  updated_at: string;
  task_type: string;
  node_type?: string;
  status: string;
  depth: number;
  retry_count: number;
  goal?: string;
  result?: Record<string, any>;
  error?: string;
}

export interface LMTrace {
  trace_id: number;
  execution_id: string;
  task_id?: string;
  module_name: string;
  created_at: string;
  model: string;
  temperature?: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost_usd?: number;
  latency_ms?: number;
  prompt?: string;
  response?: string;
  error?: string;
  metadata: Record<string, any>;
}

export interface Health {
  status: string;
  version: string;
  uptime_seconds: number;
  active_executions: number;
  storage_connected: boolean;
  cache_size: number;
  timestamp: string;
}

export interface Metrics {
  execution_id: string;
  total_lm_calls: number;
  total_tokens: number;
  total_cost_usd: number;
  average_latency_ms: number;
  task_breakdown: Record<string, Record<string, any>>;
}

export interface StatusPolling {
  execution_id: string;
  status: string;
  progress: number; // 0.0 to 1.0
  current_task_id?: string;
  current_task_goal?: string;
  completed_tasks: number;
  total_tasks: number;
  estimated_remaining_seconds?: number;
  last_updated: string;
}

export interface ExecutionData {
  execution_id: string;
  tasks: Record<string, any>[];
  summary: Record<string, any>;
  traces: Record<string, any>[];
  fallback_spans: Record<string, any>[];
}

export interface AgentProfile {
  name: string;
  description?: string;
  agents: {
    atomizer?: AgentConfig;
    planner?: AgentConfig;
    executor?: AgentConfig;
    aggregator?: AgentConfig;
    verifier?: AgentConfig;
  };
  runtime?: {
    max_depth?: number;
    timeout?: number;
  };
  toolkits?: ToolkitConfig[];
}

export interface AgentConfig {
  llm: {
    model: string;
    temperature?: number;
    max_tokens?: number;
    cache?: boolean;
  };
  prediction_strategy?: string;
  tools?: any[];
  context_defaults?: Record<string, any>;
}

export interface ToolkitConfig {
  class_name: string;
  enabled: boolean;
  toolkit_config?: Record<string, any>;
}

export interface ConfigUpdateRequest {
  profile?: string;
  overrides: Record<string, any>;
}

export interface ErrorResponse {
  error: string;
  detail?: string;
  execution_id?: string;
  timestamp: string;
}
/**
 * Agent trace types for the trace viewer (Task #17).
 * Matches GET /api/v1/traces/{run_id} response shape.
 */

export interface TraceNode {
  node_name: string
  status: 'completed' | 'running' | 'failed'
  time_ms: number
  tool_calls: string[]
  quality_score: number | null
  started_at: string
  completed_at: string | null
}

export interface AgentTrace {
  run_id: string
  nodes: TraceNode[]
  total_time_ms: number
  model_used: string
}

/**
 * SmartRouter rationale for "Why this model?" card.
 */
export interface SmartRouterRationale {
  task_type: string
  model_selected: string
  weighted_scores: {
    tokens: number
    structured: number
    tools: number
    history: number
    intent: number
  }
  total_score: number
}

/**
 * Observability dashboard data from GET /api/v1/observability/dashboard.
 */
export interface ObservabilityDashboard {
  provider: string
  model: string
  scores: {
    quality_avg: number
    latency_p50_ms: number
    latency_p95_ms: number
  }
  error_rate: number
  circuit_breaker_state: 'closed' | 'open' | 'half_open'
  sse_event_counts: Record<string, number>
  token_usage: {
    input_tokens: number
    output_tokens: number
    estimated_cost_usd: number
  }
  latency_history: Array<{
    timestamp: string
    p50: number
    p95: number
  }>
}

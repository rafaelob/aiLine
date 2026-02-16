export const DEMO_PROMPT =
  'Create an inclusive lesson plan on photosynthesis for 6th graders with ASD adaptations, aligned to NGSS standards. Include visual schedules, simplified vocabulary, and sensory-friendly activities.'
export const DEMO_GRADE = '6th Grade'
export const DEMO_SUBJECT = 'Science'
export const DEMO_PROFILE = 'tea' as const

export const DEMO_STEPS = [
  { target: 'pipeline-viewer', key: 'step_1' },
  { target: 'accessibility-btn', key: 'step_2' },
  { target: 'quality-score', key: 'step_3' },
] as const

/** Demo trace records used when API is unreachable */
export const DEMO_TRACES = [
  { run_id: 'demo-a1b2c3d4', status: 'completed', total_time_ms: 12340, node_count: 8, final_score: 92, model_used: 'claude-opus-4-6', refinement_count: 1 },
  { run_id: 'demo-e5f6g7h8', status: 'completed', total_time_ms: 8920, node_count: 6, final_score: 87, model_used: 'gpt-5.2', refinement_count: 0 },
  { run_id: 'demo-i9j0k1l2', status: 'completed', total_time_ms: 15680, node_count: 10, final_score: 95, model_used: 'gemini-3-pro', refinement_count: 2 },
  { run_id: 'demo-m3n4o5p6', status: 'completed', total_time_ms: 6780, node_count: 5, final_score: 84, model_used: 'claude-opus-4-6', refinement_count: 0 },
  { run_id: 'demo-q7r8s9t0', status: 'failed', total_time_ms: 3420, node_count: 3, final_score: null, model_used: 'gpt-5.2', refinement_count: 0 },
  { run_id: 'demo-u1v2w3x4', status: 'completed', total_time_ms: 11200, node_count: 7, final_score: 98, model_used: 'claude-opus-4-6', refinement_count: 1 },
] as const

export const DEMO_STUDENT_COUNT = 4

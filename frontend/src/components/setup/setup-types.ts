/** LLM provider identifiers */
export type LlmProvider = 'anthropic' | 'openai' | 'gemini' | 'openrouter'

/** Embedding provider identifiers */
export type EmbeddingProvider = 'gemini' | 'openai'

/** Full setup configuration state */
export interface SetupConfig {
  /* Step 1: Welcome */
  language: string

  /* Step 2: AI Provider */
  llmProvider: LlmProvider | ''
  llmApiKey: string

  /* Step 3: Embeddings */
  embeddingProvider: EmbeddingProvider
  embeddingModel: string
  embeddingDimensions: number

  /* Step 4: Agent Models */
  plannerModel: string
  executorModel: string
  qualityModel: string
  tutorModel: string

  /* Step 5: Infrastructure */
  databaseUrl: string
  redisUrl: string
  apiPort: string
  frontendPort: string

  /* Step 6: Security & Media */
  jwtSecret: string
  corsOrigins: string
  elevenlabsKey: string
}

/** Provider card metadata */
export interface ProviderOption {
  id: LlmProvider
  nameKey: string
  descKey: string
  color: string
  letter: string
}

/** Embedding provider metadata */
export interface EmbeddingOption {
  id: EmbeddingProvider
  name: string
  models: { value: string; label: string; dimensions: number }[]
}

/** Agent model selector metadata */
export interface AgentModelOption {
  id: keyof Pick<SetupConfig, 'plannerModel' | 'executorModel' | 'qualityModel' | 'tutorModel'>
  nameKey: string
  descKey: string
}

/** Step labels keyed by step index */
export const STEP_KEYS = [
  'step_welcome',
  'step_ai',
  'step_embeddings',
  'step_models',
  'step_infra',
  'step_security',
  'step_review',
] as const

export const TOTAL_STEPS = STEP_KEYS.length

/** Default configuration values */
export const DEFAULT_CONFIG: SetupConfig = {
  language: 'en',
  llmProvider: '',
  llmApiKey: '',
  embeddingProvider: 'gemini',
  embeddingModel: 'gemini-embedding-001',
  embeddingDimensions: 3072,
  plannerModel: 'anthropic:claude-sonnet-4-5-20250514',
  executorModel: 'anthropic:claude-sonnet-4-5-20250514',
  qualityModel: 'anthropic:claude-haiku-4-5-20251001',
  tutorModel: 'anthropic:claude-sonnet-4-5-20250514',
  databaseUrl: 'postgresql://ailine:ailine@db:5432/ailine',
  redisUrl: 'redis://redis:6379/0',
  apiPort: '8011',
  frontendPort: '3000',
  jwtSecret: '',
  corsOrigins: 'http://localhost:3000',
  elevenlabsKey: '',
}

/** LLM provider options */
export const LLM_PROVIDERS: ProviderOption[] = [
  { id: 'anthropic', nameKey: 'provider_anthropic', descKey: 'provider_anthropic_desc', color: '#CC785C', letter: 'A' },
  { id: 'openai', nameKey: 'provider_openai', descKey: 'provider_openai_desc', color: '#10A37F', letter: 'O' },
  { id: 'gemini', nameKey: 'provider_gemini', descKey: 'provider_gemini_desc', color: '#4285F4', letter: 'G' },
  { id: 'openrouter', nameKey: 'provider_openrouter', descKey: 'provider_openrouter_desc', color: '#6366F1', letter: 'R' },
]

/** Embedding provider options with models */
export const EMBEDDING_OPTIONS: EmbeddingOption[] = [
  {
    id: 'gemini',
    name: 'Google Gemini',
    models: [
      { value: 'gemini-embedding-001', label: 'gemini-embedding-001', dimensions: 3072 },
    ],
  },
  {
    id: 'openai',
    name: 'OpenAI',
    models: [
      { value: 'text-embedding-3-large', label: 'text-embedding-3-large', dimensions: 3072 },
      { value: 'text-embedding-3-small', label: 'text-embedding-3-small', dimensions: 1536 },
    ],
  },
]

/** Agent model selectors */
export const AGENT_MODELS: AgentModelOption[] = [
  { id: 'plannerModel', nameKey: 'agent_planner', descKey: 'agent_planner_desc' },
  { id: 'executorModel', nameKey: 'agent_executor', descKey: 'agent_executor_desc' },
  { id: 'qualityModel', nameKey: 'agent_quality', descKey: 'agent_quality_desc' },
  { id: 'tutorModel', nameKey: 'agent_tutor', descKey: 'agent_tutor_desc' },
]

/** Model options per provider for agent dropdowns */
export const MODEL_OPTIONS: Record<string, { value: string; label: string }[]> = {
  anthropic: [
    { value: 'anthropic:claude-sonnet-4-5-20250514', label: 'Claude Sonnet 4.5' },
    { value: 'anthropic:claude-haiku-4-5-20251001', label: 'Claude Haiku 4.5' },
    { value: 'anthropic:claude-opus-4-6', label: 'Claude Opus 4.6' },
  ],
  openai: [
    { value: 'openai:gpt-5.2', label: 'GPT-5.2' },
    { value: 'openai:gpt-5-mini', label: 'GPT-5 Mini' },
  ],
  gemini: [
    { value: 'google-gla:gemini-3-pro-preview', label: 'Gemini 3 Pro' },
    { value: 'google-gla:gemini-3-flash-preview', label: 'Gemini 3 Flash' },
  ],
  openrouter: [
    { value: 'openrouter:anthropic/claude-sonnet-4.5', label: 'Claude Sonnet 4.5 (via OR)' },
    { value: 'openrouter:openai/gpt-5.2', label: 'GPT-5.2 (via OR)' },
    { value: 'openrouter:google/gemini-3-pro', label: 'Gemini 3 Pro (via OR)' },
  ],
}

/**
 * Tutor chat types for the frontend.
 */

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

export interface TutorChatRequest {
  message: string
  session_id?: string
  tutor_id?: string
  locale?: string
}

export interface TutorChatResponse {
  reply: string
  session_id: string
  mermaid_diagram?: string
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
}

export interface ChatRequest {
  repo_id: string;
  message: string;
  history?: ChatMessage[];
}

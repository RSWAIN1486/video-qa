export type ModelStatus = {
  model_id: string;
  loaded: boolean;
  loading: boolean;
  device: string | null;
  dtype: string | null;
  last_error: string | null;
  cold_start_required: boolean;
};

export type VideoRecord = {
  id: string;
  filename: string;
  duration_sec: number;
  width: number;
  height: number;
  size_bytes: number;
  created_at: string;
  source: 'sample' | 'upload';
  content_url: string;
};

export type QaMessage = {
  id: string;
  role: 'user' | 'assistant' | 'system';
  text: string;
  status?: string;
  latency_ms?: number;
};

export type QaRequest = {
  video_id: string;
  question: string;
  max_fps?: number;
  max_new_tokens?: number;
};

export type StreamHandlers = {
  onStatus?: (data: { status: string; run_id?: string }) => void;
  onToken?: (data: { text: string; run_id?: string }) => void;
  onFinal?: (data: { answer: string; latency_ms: number; run_id?: string }) => void;
  onError?: (data: { message: string; code?: string; run_id?: string }) => void;
};


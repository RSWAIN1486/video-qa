import type { ModelStatus, QaRequest, StreamHandlers, VideoRecord } from '$lib/types';

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail ?? `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function getModelStatus(): Promise<ModelStatus> {
  return readJson<ModelStatus>(await fetch('/api/model/status'));
}

export async function listVideos(): Promise<VideoRecord[]> {
  return readJson<VideoRecord[]>(await fetch('/api/videos'));
}

export async function uploadVideo(file: File): Promise<VideoRecord> {
  const form = new FormData();
  form.append('file', file);
  return readJson<VideoRecord>(
    await fetch('/api/videos', {
      method: 'POST',
      body: form
    })
  );
}

export async function streamQa(payload: QaRequest, handlers: StreamHandlers): Promise<void> {
  const response = await fetch('/api/qa/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!response.ok || !response.body) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail ?? `QA request failed with ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split('\n\n');
    buffer = events.pop() ?? '';
    for (const eventText of events) {
      dispatchEventText(eventText, handlers);
    }
  }
  if (buffer.trim()) {
    dispatchEventText(buffer, handlers);
  }
}

function dispatchEventText(eventText: string, handlers: StreamHandlers): void {
  const lines = eventText.split('\n');
  const event = lines.find((line) => line.startsWith('event:'))?.slice(6).trim();
  const dataLine = lines.find((line) => line.startsWith('data:'))?.slice(5).trim();
  if (!event || !dataLine) return;

  const data = JSON.parse(dataLine);
  if (event === 'status') handlers.onStatus?.(data);
  if (event === 'token') handlers.onToken?.(data);
  if (event === 'final') handlers.onFinal?.(data);
  if (event === 'error') handlers.onError?.(data);
}


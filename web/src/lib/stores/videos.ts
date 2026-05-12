import { writable } from 'svelte/store';
import type { VideoRecord } from '$lib/types';
import { listVideos } from '$lib/services/api';

export const videos = writable<VideoRecord[]>([]);
export const selectedVideo = writable<VideoRecord | null>(null);
export const videoError = writable<string | null>(null);

export async function refreshVideos(): Promise<void> {
  try {
    const records = await listVideos();
    videos.set(records);
    selectedVideo.update((current) => current ?? records[0] ?? null);
    videoError.set(null);
  } catch (error) {
    videoError.set(error instanceof Error ? error.message : 'Could not load videos.');
  }
}


import { writable } from 'svelte/store';
import type { ModelStatus } from '$lib/types';
import { getModelStatus } from '$lib/services/api';

export const modelStatus = writable<ModelStatus | null>(null);
export const modelStatusError = writable<string | null>(null);

export async function refreshModelStatus(): Promise<void> {
  try {
    modelStatus.set(await getModelStatus());
    modelStatusError.set(null);
  } catch (error) {
    modelStatusError.set(error instanceof Error ? error.message : 'Could not load model status.');
  }
}


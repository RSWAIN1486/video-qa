import { writable } from 'svelte/store';
import type { ModelStatus } from '$lib/types';
import { getModelStatus, loadModel } from '$lib/services/api';

export const modelStatus = writable<ModelStatus | null>(null);
export const modelStatusError = writable<string | null>(null);
export const modelLoading = writable(false);

export async function refreshModelStatus(): Promise<void> {
  try {
    modelStatus.set(await getModelStatus());
    modelStatusError.set(null);
  } catch (error) {
    modelStatusError.set(error instanceof Error ? error.message : 'Could not load model status.');
  }
}

export async function warmLoadModel(): Promise<void> {
  modelLoading.set(true);
  modelStatusError.set(null);
  modelStatus.update((status) =>
    status ? { ...status, loading: true, cold_start_required: true } : status
  );
  try {
    modelStatus.set(await loadModel());
  } catch (error) {
    modelStatusError.set(error instanceof Error ? error.message : 'Could not load model.');
  } finally {
    modelLoading.set(false);
  }
}

<script lang="ts">
  import { CheckCircle2, CircleAlert, Loader2, Server } from 'lucide-svelte';
  import type { ModelStatus } from '$lib/types';

  export let status: ModelStatus | null;
  export let error: string | null = null;
</script>

<div class="status-badge" class:error-state={Boolean(error || status?.last_error)}>
  {#if error || status?.last_error}
    <CircleAlert size={16} />
    <span>{error ?? status?.last_error}</span>
  {:else if status?.loading}
    <Loader2 size={16} class="icon-spin" />
    <span>Loading {status.model_id}</span>
  {:else if status?.loaded}
    <CheckCircle2 size={16} />
    <span>{status.model_id} ready</span>
  {:else}
    <Server size={16} />
    <span>{status?.model_id ?? 'Molmo2-8B'} cold start</span>
  {/if}
</div>

<style>
  .status-badge {
    display: inline-flex;
    min-height: 32px;
    align-items: center;
    gap: 8px;
    border: 1px solid rgba(132, 204, 163, 0.32);
    border-radius: 8px;
    padding: 6px 10px;
    background: rgba(31, 52, 42, 0.72);
    color: #d9f8e6;
    font-size: 13px;
    line-height: 1.25;
    overflow-wrap: anywhere;
  }

  .error-state {
    border-color: rgba(248, 113, 113, 0.38);
    background: rgba(88, 28, 28, 0.44);
    color: #fecaca;
  }
</style>


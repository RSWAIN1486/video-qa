<script lang="ts">
  import { Clock, Loader2, Send, Sparkles } from 'lucide-svelte';
  import type { QaMessage, VideoRecord } from '$lib/types';

  export let selectedVideo: VideoRecord | null = null;
  export let messages: QaMessage[] = [];
  export let busy = false;
  export let statusText = '';
  export let onAsk: (question: string) => Promise<void>;

  let question = '';
  const samples = ['what do you see in the video', 'when did the woman in red turn backward'];

  async function submit(text = question) {
    const trimmed = text.trim();
    if (!trimmed || busy || !selectedVideo) return;
    question = '';
    await onAsk(trimmed);
  }
</script>

<section class="panel">
  <div class="panel-heading">
    <div>
      <p>Ask about the video</p>
      <h2>Video QA</h2>
    </div>
    {#if busy}
      <div class="run-state"><Loader2 size={15} class="icon-spin" /> {statusText || 'Working'}</div>
    {:else}
      <div class="run-state idle"><Sparkles size={15} /> Ready</div>
    {/if}
  </div>

  <div class="sample-row">
    {#each samples as sample}
      <button disabled={!selectedVideo || busy} on:click={() => submit(sample)}>{sample}</button>
    {/each}
  </div>

  <div class="thread" aria-live="polite">
    {#if messages.length === 0}
      <div class="empty-thread">
        <Sparkles size={28} />
        <span>Choose the sample video and ask what is happening.</span>
      </div>
    {/if}
    {#each messages as message}
      <article class:assistant={message.role === 'assistant'} class="message">
        <div class="avatar">{message.role === 'user' ? 'You' : 'AI'}</div>
        <div class="bubble">
          <p>{message.text}</p>
          {#if message.latency_ms}
            <span><Clock size={13} /> {(message.latency_ms / 1000).toFixed(1)}s</span>
          {/if}
        </div>
      </article>
    {/each}
  </div>

  <form on:submit|preventDefault={() => submit()}>
    <textarea
      bind:value={question}
      rows="2"
      disabled={!selectedVideo || busy}
      placeholder={selectedVideo ? 'Ask about the selected video...' : 'Select a video first'}
    ></textarea>
    <button disabled={!selectedVideo || busy || !question.trim()} aria-label="Send question">
      {#if busy}
        <Loader2 size={18} class="icon-spin" />
      {:else}
        <Send size={18} />
      {/if}
    </button>
  </form>
</section>

<style>
  .panel {
    display: flex;
    min-width: 0;
    min-height: 620px;
    flex-direction: column;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    background: rgba(20, 26, 24, 0.92);
    padding: 18px;
  }

  .panel-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 12px;
  }

  p {
    margin: 0 0 4px;
    color: #95a39b;
    font-size: 12px;
    text-transform: uppercase;
  }

  h2 {
    margin: 0;
    color: #f7faf8;
    font-size: 20px;
  }

  .run-state {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    border-radius: 8px;
    padding: 6px 9px;
    background: rgba(59, 130, 246, 0.18);
    color: #bfdbfe;
    font-size: 12px;
  }

  .run-state.idle {
    background: rgba(52, 211, 153, 0.14);
    color: #c8f8dc;
  }

  .sample-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;
  }

  .sample-row button {
    border: 1px solid rgba(132, 204, 163, 0.26);
    border-radius: 8px;
    padding: 8px 10px;
    background: rgba(35, 68, 51, 0.62);
    color: #e8fff0;
    font-size: 13px;
  }

  .thread {
    display: flex;
    min-height: 0;
    flex: 1;
    flex-direction: column;
    gap: 14px;
    overflow-y: auto;
    padding: 8px 2px 14px;
  }

  .empty-thread {
    display: grid;
    min-height: 240px;
    place-items: center;
    gap: 10px;
    color: #85928b;
    text-align: center;
  }

  .message {
    display: grid;
    grid-template-columns: 42px minmax(0, 1fr);
    gap: 10px;
  }

  .avatar {
    display: grid;
    width: 36px;
    height: 36px;
    place-items: center;
    border-radius: 50%;
    background: #244835;
    color: #d9fbe6;
    font-size: 12px;
    font-weight: 700;
  }

  .assistant .avatar {
    background: #9b2f74;
    color: #fff1fa;
  }

  .bubble {
    min-width: 0;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 8px;
    padding: 12px 14px;
    background: rgba(255, 255, 255, 0.04);
  }

  .bubble p {
    margin: 0;
    color: #edf6f0;
    font-size: 15px;
    line-height: 1.55;
    text-transform: none;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
  }

  .bubble span {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    margin-top: 8px;
    color: #95a39b;
    font-size: 12px;
  }

  form {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 46px;
    gap: 10px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    padding-top: 14px;
  }

  textarea {
    width: 100%;
    resize: none;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 11px 12px;
    background: rgba(255, 255, 255, 0.045);
    color: #f7faf8;
    outline: none;
  }

  textarea:focus {
    border-color: rgba(132, 204, 163, 0.6);
  }

  form button {
    display: grid;
    width: 46px;
    height: 46px;
    place-items: center;
    border: 0;
    border-radius: 8px;
    background: #43c779;
    color: #062411;
  }

  @media (max-width: 980px) {
    .panel {
      min-height: 540px;
    }
  }
</style>

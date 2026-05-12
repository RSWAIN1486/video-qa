<script lang="ts">
  import { Film, Upload } from 'lucide-svelte';
  import type { VideoRecord } from '$lib/types';

  export let videos: VideoRecord[] = [];
  export let selected: VideoRecord | null = null;
  export let uploading = false;
  export let error: string | null = null;
  export let onSelect: (video: VideoRecord) => void;
  export let onUpload: (file: File) => Promise<void>;

  async function handleFile(event: Event) {
    const input = event.currentTarget as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    await onUpload(file);
    input.value = '';
  }

  const formatSeconds = (value: number) => `${value.toFixed(1)}s`;
  const formatSize = (value: number) => `${(value / 1024 / 1024).toFixed(1)} MB`;
</script>

<section class="panel">
  <div class="panel-heading">
    <div>
      <p>Video</p>
      <h2>{selected?.filename ?? 'Select a video'}</h2>
    </div>
    <label class="upload-button" aria-label="Upload video">
      <Upload size={17} />
      <span>{uploading ? 'Uploading' : 'Upload'}</span>
      <input disabled={uploading} type="file" accept="video/mp4,video/quicktime,video/webm" on:change={handleFile} />
    </label>
  </div>

  <div class="preview">
    {#if selected}
      <video src={selected.content_url} controls playsinline>
        <track kind="captions" />
      </video>
    {:else}
      <div class="empty">
        <Film size={42} />
      </div>
    {/if}
  </div>

  {#if selected}
    <div class="meta">
      <span>{selected.width}x{selected.height}</span>
      <span>{formatSeconds(selected.duration_sec)}</span>
      <span>{formatSize(selected.size_bytes)}</span>
      <span>{selected.source}</span>
    </div>
  {/if}

  {#if error}
    <p class="error">{error}</p>
  {/if}

  <div class="video-list">
    {#each videos as video}
      <button class:active={selected?.id === video.id} on:click={() => onSelect(video)}>
        <Film size={15} />
        <span>{video.filename}</span>
      </button>
    {/each}
  </div>
</section>

<style>
  .panel {
    min-width: 0;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    background: rgba(20, 26, 24, 0.92);
    padding: 18px;
  }

  .panel-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    margin-bottom: 14px;
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
    font-weight: 650;
    overflow-wrap: anywhere;
  }

  .upload-button {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    border: 1px solid rgba(132, 204, 163, 0.3);
    border-radius: 8px;
    padding: 9px 12px;
    background: #234433;
    color: #e9fff1;
    font-size: 14px;
    white-space: nowrap;
  }

  input[type='file'] {
    display: none;
  }

  .preview {
    display: grid;
    width: 100%;
    aspect-ratio: 16 / 9;
    place-items: center;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    background: #070908;
  }

  video {
    width: 100%;
    height: 100%;
    object-fit: contain;
  }

  .empty {
    color: #65746b;
  }

  .meta {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
  }

  .meta span {
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 4px 8px;
    color: #b7c4bd;
    font-size: 12px;
  }

  .video-list {
    display: grid;
    gap: 8px;
    margin-top: 14px;
  }

  .video-list button {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 10px;
    background: rgba(255, 255, 255, 0.03);
    color: #cad7d0;
    text-align: left;
  }

  .video-list button span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .video-list button.active {
    border-color: rgba(132, 204, 163, 0.46);
    background: rgba(50, 96, 70, 0.5);
    color: #f4fff8;
  }

  .error {
    margin-top: 12px;
    color: #fecaca;
    font-size: 13px;
    text-transform: none;
  }

  @media (max-width: 720px) {
    .panel-heading {
      align-items: flex-start;
      flex-direction: column;
    }
  }
</style>

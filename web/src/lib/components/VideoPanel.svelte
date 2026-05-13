<script lang="ts">
  import { tick } from 'svelte';
  import { CheckCircle2, Film, Loader2, Upload } from 'lucide-svelte';
  import type { VideoPoint, VideoRecord } from '$lib/types';

  export let videos: VideoRecord[] = [];
  export let selected: VideoRecord | null = null;
  export let uploading = false;
  export let error: string | null = null;
  export let uploadStatus: string | null = null;
  export let highlightPoint: VideoPoint | null = null;
  export let onSelect: (video: VideoRecord) => void;
  export let onUpload: (file: File) => Promise<void>;

  let videoEl: HTMLVideoElement | null = null;
  let previewEl: HTMLDivElement | null = null;
  let lastPointKey = '';

  async function handleFile(event: Event) {
    const input = event.currentTarget as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    await onUpload(file);
    input.value = '';
  }

  const formatSeconds = (value: number) => `${value.toFixed(1)}s`;
  const formatSize = (value: number) => `${(value / 1024 / 1024).toFixed(1)} MB`;

  $: if (highlightPoint && selected && videoEl) {
    const pointKey = `${selected.id}:${highlightPoint.time_sec}:${highlightPoint.x}:${highlightPoint.y}`;
    if (pointKey !== lastPointKey) {
      lastPointKey = pointKey;
      seekToPoint(highlightPoint);
    }
  }

  async function seekToPoint(point: VideoPoint) {
    await tick();
    if (!videoEl || !selected) return;
    videoEl.currentTime = Math.max(0, Math.min(point.time_sec, selected.duration_sec));
    videoEl.pause();
  }

  function pointStyle(point: VideoPoint): string {
    if (!selected || !previewEl) return '';
    const boxW = previewEl.clientWidth || selected.width;
    const boxH = previewEl.clientHeight || selected.height;
    const videoAspect = selected.width / selected.height;
    const boxAspect = boxW / boxH;
    let renderedW = boxW;
    let renderedH = boxH;
    let offsetX = 0;
    let offsetY = 0;

    if (boxAspect > videoAspect) {
      renderedH = boxH;
      renderedW = renderedH * videoAspect;
      offsetX = (boxW - renderedW) / 2;
    } else {
      renderedW = boxW;
      renderedH = renderedW / videoAspect;
      offsetY = (boxH - renderedH) / 2;
    }

    const x = offsetX + (point.x / selected.width) * renderedW;
    const y = offsetY + (point.y / selected.height) * renderedH;
    return `left:${x}px;top:${y}px;`;
  }
</script>

<section class="panel">
  <div class="panel-heading">
    <div>
      <p>Video</p>
      <h2>{selected?.filename ?? 'Select a video'}</h2>
    </div>
    {#if selected}
      <div class="loaded-badge">
        <CheckCircle2 size={16} />
        <span>Video loaded</span>
      </div>
    {/if}
    <label class="upload-button" aria-label="Upload video">
      {#if uploading}
        <Loader2 size={17} class="icon-spin" />
      {:else}
        <Upload size={17} />
      {/if}
      <span>{uploading ? 'Uploading' : 'Upload'}</span>
      <input disabled={uploading} type="file" accept="video/mp4,video/quicktime,video/webm" on:change={handleFile} />
    </label>
  </div>

  <div class="preview" bind:this={previewEl}>
    {#if selected}
      <video bind:this={videoEl} src={selected.content_url} controls playsinline>
        <track kind="captions" />
      </video>
      {#if highlightPoint}
        <div class="point-marker" style={pointStyle(highlightPoint)} aria-label="Object point">
          <span></span>
        </div>
      {/if}
    {:else}
      <div class="empty">
        <Film size={42} />
      </div>
    {/if}
  </div>

  {#if selected}
    <div class="meta">
      <span class="ready-chip"><CheckCircle2 size={13} /> Loaded</span>
      <span>{selected.width}x{selected.height}</span>
      <span>{formatSeconds(selected.duration_sec)}</span>
      <span>{formatSize(selected.size_bytes)}</span>
      <span>{selected.source}</span>
    </div>
  {/if}

  {#if error}
    <p class="error">{error}</p>
  {:else if uploadStatus}
    <p class="status">{uploadStatus}</p>
  {/if}

  <div class="video-list">
    {#if videos.length === 0}
      <div class="empty-list">No videos loaded yet. Upload a short clip to enable questions.</div>
    {:else}
      {#each videos as video}
        <button class:active={selected?.id === video.id} on:click={() => onSelect(video)}>
          <Film size={15} />
          <span>{video.filename}</span>
          {#if selected?.id === video.id}
            <CheckCircle2 size={15} />
          {/if}
        </button>
      {/each}
    {/if}
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

  .loaded-badge {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    border: 1px solid rgba(132, 204, 163, 0.28);
    border-radius: 8px;
    padding: 7px 10px;
    background: rgba(35, 68, 51, 0.5);
    color: #c8f8dc;
    font-size: 13px;
    font-weight: 700;
    white-space: nowrap;
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
    position: relative;
    display: grid;
    width: 100%;
    aspect-ratio: 16 / 9;
    place-items: center;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    background: #070908;
  }

  .point-marker {
    position: absolute;
    z-index: 2;
    width: 30px;
    height: 30px;
    transform: translate(-50%, -50%);
    border: 2px solid #ff4fa3;
    border-radius: 50%;
    box-shadow: 0 0 0 6px rgba(255, 79, 163, 0.2), 0 0 24px rgba(255, 79, 163, 0.62);
    pointer-events: none;
  }

  .point-marker span {
    position: absolute;
    left: 50%;
    top: 50%;
    width: 6px;
    height: 6px;
    transform: translate(-50%, -50%);
    border-radius: 50%;
    background: #ff4fa3;
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
    display: inline-flex;
    align-items: center;
    gap: 5px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 4px 8px;
    color: #b7c4bd;
    font-size: 12px;
  }

  .meta .ready-chip {
    border-color: rgba(132, 204, 163, 0.35);
    background: rgba(35, 68, 51, 0.42);
    color: #c8f8dc;
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
    flex: 1;
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

  .status {
    margin-top: 12px;
    color: #c8f8dc;
    font-size: 13px;
    text-transform: none;
  }

  .empty-list {
    border: 1px dashed rgba(255, 255, 255, 0.14);
    border-radius: 8px;
    padding: 12px;
    color: #95a39b;
    font-size: 13px;
    line-height: 1.4;
  }

  @media (max-width: 720px) {
    .panel-heading {
      align-items: flex-start;
      flex-direction: column;
    }
  }
</style>

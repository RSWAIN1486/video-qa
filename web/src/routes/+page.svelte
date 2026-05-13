<script lang="ts">
  import { onMount } from 'svelte';
  import { RefreshCcw, ShieldCheck, Zap } from 'lucide-svelte';
  import ChatPanel from '$lib/components/ChatPanel.svelte';
  import StatusBadge from '$lib/components/StatusBadge.svelte';
  import VideoPanel from '$lib/components/VideoPanel.svelte';
  import { streamQa, uploadVideo } from '$lib/services/api';
  import {
    modelLoading,
    modelStatus,
    modelStatusError,
    refreshModelStatus,
    warmLoadModel
  } from '$lib/stores/model';
  import { refreshVideos, selectedVideo, videoError, videos } from '$lib/stores/videos';
  import type { QaMessage, VideoRecord } from '$lib/types';
  import { makeClientId } from '$lib/utils/id';

  let messages: QaMessage[] = [];
  let busy = false;
  let statusText = '';
  let uploading = false;
  let uploadStatus: string | null = null;

  onMount(async () => {
    await Promise.all([refreshModelStatus(), refreshVideos()]);
  });

  function selectVideo(video: VideoRecord) {
    selectedVideo.set(video);
  }

  async function handleUpload(file: File) {
    uploading = true;
    uploadStatus = `Uploading ${file.name}...`;
    videoError.set(null);
    try {
      const record = await uploadVideo(file);
      await refreshVideos();
      selectedVideo.set(record);
      uploadStatus = `Uploaded ${record.filename}. You can ask a question now.`;
    } catch (error) {
      videoError.set(error instanceof Error ? error.message : 'Upload failed.');
      uploadStatus = null;
    } finally {
      uploading = false;
    }
  }

  async function ask(question: string) {
    const video = $selectedVideo;
    if (!video) return;

    const userMessage: QaMessage = { id: makeClientId('user'), role: 'user', text: question };
    const assistantMessage: QaMessage = {
      id: makeClientId('assistant'),
      role: 'assistant',
      text: '',
      status: 'queued'
    };
    messages = [...messages, userMessage, assistantMessage];
    busy = true;
    statusText = 'Queued';

    try {
      await streamQa(
        { video_id: video.id, question },
        {
          onStatus: (data) => {
            statusText = data.status.replaceAll('_', ' ');
            messages = messages.map((message) =>
              message.id === assistantMessage.id ? { ...message, status: data.status } : message
            );
          },
          onToken: (data) => {
            messages = messages.map((message) =>
              message.id === assistantMessage.id ? { ...message, text: data.text } : message
            );
          },
          onFinal: (data) => {
            messages = messages.map((message) =>
              message.id === assistantMessage.id
                ? { ...message, text: data.answer, latency_ms: data.latency_ms, status: 'complete' }
                : message
            );
          },
          onError: (data) => {
            messages = messages.map((message) =>
              message.id === assistantMessage.id
                ? { ...message, text: data.message, status: 'error' }
                : message
            );
          }
        }
      );
      await refreshModelStatus();
    } catch (error) {
      messages = messages.map((message) =>
        message.id === assistantMessage.id
          ? {
              ...message,
              text: error instanceof Error ? error.message : 'Video QA failed.',
              status: 'error'
            }
          : message
      );
    } finally {
      busy = false;
      statusText = '';
    }
  }
</script>

<main class="shell">
  <header>
    <div>
      <p>Local video intelligence</p>
      <h1>Video QA Demo</h1>
    </div>
    <div class="header-actions">
      <StatusBadge status={$modelStatus} error={$modelStatusError} />
      <button
        class="load-button"
        disabled={$modelLoading || $modelStatus?.loaded}
        on:click={warmLoadModel}
        aria-label="Load model into memory"
      >
        <Zap size={17} />
        <span>{$modelLoading ? 'Loading' : $modelStatus?.loaded ? 'Loaded' : 'Load model'}</span>
      </button>
      <button class="icon-button" on:click={refreshModelStatus} aria-label="Refresh model status" title="Refresh model status">
        <RefreshCcw size={18} />
      </button>
    </div>
  </header>

  <section class="privacy-strip">
    <ShieldCheck size={17} />
    <span>Local-first demo: videos stay in local storage. V1 supports short clips up to 60 seconds; long-video chunking comes next.</span>
  </section>

  <div class="workspace">
    <VideoPanel
      videos={$videos}
      selected={$selectedVideo}
      uploading={uploading}
      error={$videoError}
      uploadStatus={uploadStatus}
      onSelect={selectVideo}
      onUpload={handleUpload}
    />
    <ChatPanel
      selectedVideo={$selectedVideo}
      {messages}
      {busy}
      {statusText}
      onAsk={ask}
    />
  </div>
</main>

<style>
  .shell {
    width: min(1440px, 100%);
    margin: 0 auto;
    padding: 24px;
  }

  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 14px;
  }

  header p {
    margin: 0 0 4px;
    color: #84cca3;
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
  }

  h1 {
    margin: 0;
    color: #f8fbf9;
    font-size: clamp(28px, 4vw, 44px);
    font-weight: 760;
    letter-spacing: 0;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .icon-button {
    display: grid;
    width: 36px;
    height: 36px;
    place-items: center;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.04);
    color: #dce8e1;
  }

  .load-button {
    display: inline-flex;
    min-height: 36px;
    align-items: center;
    gap: 8px;
    border: 1px solid rgba(132, 204, 163, 0.32);
    border-radius: 8px;
    padding: 7px 11px;
    background: #24533a;
    color: #edfff3;
    font-weight: 700;
    white-space: nowrap;
  }

  .privacy-strip {
    display: flex;
    align-items: center;
    gap: 9px;
    min-height: 38px;
    margin-bottom: 18px;
    border: 1px solid rgba(132, 204, 163, 0.18);
    border-radius: 8px;
    padding: 9px 12px;
    background: rgba(34, 55, 44, 0.64);
    color: #bfd4c7;
    font-size: 13px;
    line-height: 1.35;
  }

  .workspace {
    display: grid;
    grid-template-columns: minmax(340px, 0.95fr) minmax(420px, 1.05fr);
    gap: 18px;
    align-items: start;
  }

  @media (max-width: 980px) {
    .shell {
      padding: 16px;
    }

    header {
      align-items: flex-start;
      flex-direction: column;
    }

    .header-actions {
      width: 100%;
      justify-content: space-between;
    }

    .workspace {
      grid-template-columns: 1fr;
    }
  }
</style>

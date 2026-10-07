<script setup>
import { onUnmounted, ref } from 'vue';
import { decodeText, readRemoteText } from './lib/files.js';
import { safeUrl } from './lib/urls.js';

const dialog = ref(), name = ref(''), text = ref(''), image = ref(''), error = ref('');
let request, objectUrl;
function close() {
  request?.abort();
  if (objectUrl) URL.revokeObjectURL(objectUrl);
  objectUrl = null;
  text.value = image.value = '';
}
async function open(attachment) {
  close();
  const controller = request = new AbortController();
  name.value = attachment.original_name;
  error.value = '';
  if (!dialog.value.open) dialog.value.showModal();
  try {
    if (attachment.kind === 'text') {
      const value = attachment.upload ? decodeText(await attachment.upload.arrayBuffer())
        : await readRemoteText(await fetch(safeUrl(attachment.file.url, false), { signal: controller.signal }));
      if (!controller.signal.aborted) text.value = value;
    } else {
      image.value = attachment.upload ? (objectUrl = URL.createObjectURL(attachment.upload)) : safeUrl(attachment.file.url, false).href;
    }
  } catch (failure) { if (!controller.signal.aborted) error.value = failure.message; }
}
defineExpose({ open });
onUnmounted(close);
</script>

<template>
  <dialog ref="dialog" id="file-viewer" aria-labelledby="file-viewer-title" @close="close" @click.self="dialog.close()">
    <header class="heading"><h2 id="file-viewer-title">{{ name }}</h2><button type="button" aria-label="Close file" @click="dialog.close()">×</button></header>
    <p class="error" role="status">{{ error }}</p>
    <img v-if="image" :src="image" :alt="name" @error="error = 'The image could not be opened.'">
    <pre v-else>{{ text }}</pre>
  </dialog>
</template>

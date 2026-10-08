<script setup>
import { reactive, ref } from 'vue';
import CommentCard from './CommentCard.vue';
import CommentEditor from './CommentEditor.vue';
import { renderMessage } from './lib/entities.js';
import { validateFile } from './lib/files.js';
import { safeUrl } from './lib/urls.js';
import { captchaToken } from './lib/captcha.js';

const props = defineProps({ createUrl: String, siteKey: String, csrfToken: String, sort: String, reload: Function });
defineEmits(['open']);
const form = ref(), textInput = ref();
const draft = reactive({ username: '', email: '', homepage: '', text: '' });
const reply = ref(null), quote = ref(null), preview = ref(null), file = ref(null);
const errors = ref({}), status = ref(''), posting = ref(false), entities = ref([]);
const fields = [['username', 'User Name', 'text', 80], ['email', 'E-mail', 'email', 254], ['homepage', 'Home page', 'url', 2048]];

function select(comment, kind) {
  (kind === 'reply' ? reply : quote).value = comment;
  preview.value = null;
  textInput.value.focus();
}
defineExpose({ select });

function showPreview() {
  errors.value = {};
  preview.value = null;
  try {
    const html = renderMessage(draft.text, entities.value);
    if (form.value.reportValidity()) preview.value = { ...draft, rendered_text: html, created_at: new Date().toISOString(), quoted_comment: quote.value };
  } catch (error) { errors.value.text = error.message; }
}

function updateText(message) {
  draft.text = message.text;
  entities.value = message.entities;
  preview.value = null;
}

async function chooseFile(event) {
  const input = event.target, upload = input.files[0];
  file.value = null;
  errors.value.attachment = '';
  try {
    await validateFile(upload);
    if (input.files[0] === upload) file.value = upload;
  } catch (error) { if (input.files[0] === upload) errors.value.attachment = error.message; }
}

async function submit() {
  if (posting.value) return;
  errors.value = {};
  try { renderMessage(draft.text, entities.value); }
  catch (error) { errors.value.text = error.message; return; }
  if (!form.value.reportValidity()) return;
  // Lock before async validation as well as the request to prevent double posts.
  posting.value = true;
  let saved = false;
  try {
    try { await validateFile(form.value.elements.attachment.files[0]); }
    catch (error) { errors.value.attachment = error.message; return; }
    const data = new FormData(form.value);
    data.set('text', draft.text);
    data.set('entities', JSON.stringify(entities.value));
    status.value = 'Verifying…';
    try { data.set('g-recaptcha-response', await captchaToken(props.siteKey)); }
    catch {
      errors.value.recaptcha = 'Verification is unavailable. Please try again.';
      status.value = '';
      return;
    }
    data.set('sort', props.sort);
    status.value = 'Posting comment…';
    const response = await fetch(safeUrl(props.createUrl), {
      method: 'POST', body: data, headers: { 'X-CSRFToken': props.csrfToken, Accept: 'application/json' },
    });
    saved = response.ok;
    const result = await response.json();
    if (!saved) { errors.value = result.errors || { __all__: 'Your comment could not be posted.' }; status.value = 'Please check your comment.'; return; }
    Object.keys(draft).forEach(key => { draft[key] = ''; });
    form.value.reset();
    reply.value = quote.value = preview.value = file.value = null;
    textInput.value.clear();
    const url = safeUrl(result.list_url || location.href);
    if (Number.isSafeInteger(result.comment_id)) url.hash = `comment-${result.comment_id}`;
    const refreshed = await props.reload(url);
    status.value = refreshed ? 'Your comment has been posted.' : 'Your comment was posted. Refresh the discussion to see it.';
  } catch {
    status.value = saved ? 'Your comment was posted. Refresh the discussion to see it.' : 'We could not confirm your submission. Check the discussion before trying again.';
  } finally {
    posting.value = false;
  }
}

</script>

<template>
  <form ref="form" id="comment-form" class="panel composer" method="post" :action="createUrl" enctype="multipart/form-data" @submit.prevent="submit" @input="preview = null">
    <h2>Add a comment</h2><small>Fields marked * are required.</small>
    <p v-if="reply">Replying to {{ reply.username }} <button type="button" data-cancel-reply @click="reply = null; preview = null">Cancel reply</button></p>
    <p v-if="quote">Quoting {{ quote.username }} <button type="button" data-cancel-quote @click="quote = null; preview = null">Remove quote</button></p>
    <p class="error" role="alert">{{ [].concat(errors.__all__ || []).join(' ') }}</p>
    <div class="fields">
      <label v-for="[name, label, type, limit] in fields" :key="name" :for="`id_${name}`">
        {{ label }} {{ name === 'homepage' ? '' : '*' }}
        <input :id="`id_${name}`" v-model="draft[name]" :name="name" :type="type" :maxlength="limit" :required="name !== 'homepage'"
               :pattern="name === 'username' ? '[A-Za-z0-9]+' : name === 'homepage' ? 'https?://.+' : undefined" :aria-describedby="`${name}-errors`">
        <span :id="`${name}-errors`" class="error">{{ [].concat(errors[name] || []).join(' ') }}</span>
      </label>
    </div>
    <label id="text-label">Text *</label>
    <CommentEditor ref="textInput" @change="updateText" />
    <p id="text-errors" class="error" role="alert">{{ [].concat(errors.text || []).join(' ') }}</p>
    <label for="id_attachment">Image or text file</label><input id="id_attachment" name="attachment" type="file" accept=".jpg,.jpeg,.gif,.png,.txt" @change="chooseFile">
    <small>JPG, GIF or PNG up to 10 MB, resized to 320 × 240. UTF-8 TXT up to 100 KB.</small>
    <p id="attachment-errors" class="error">{{ [].concat(errors.attachment || []).join(' ') }}</p>
    <button v-if="file" type="button" data-preview-file @click="$emit('open', { upload: file, original_name: file.name, kind: /\.txt$/i.test(file.name) ? 'text' : 'image' })">View selected file</button>
    <p v-if="!siteKey">Verification is currently unavailable. Please try again later.</p>
    <p id="recaptcha-errors" class="error" role="alert">{{ [].concat(errors.recaptcha || []).join(' ') }}</p>
    <input type="hidden" name="csrfmiddlewaretoken" :value="csrfToken"><input type="hidden" name="parent_id" :value="reply?.pk || ''"><input type="hidden" name="quoted_comment_id" :value="quote?.pk || ''">
    <div class="buttons"><button class="primary" data-submit :disabled="posting || !createUrl || !siteKey">Post comment</button><button type="button" data-preview @click="showPreview">Preview</button></div>
    <p data-form-status role="status">{{ status }}</p>
    <section v-if="preview" id="comment-preview"><h3>Preview</h3><CommentCard :comment="preview" :sort="sort" preview /></section>
  </form>
</template>

<script setup>
import { nextTick, onMounted, onUnmounted, reactive, ref } from 'vue';
import CommentCard from './CommentCard.vue';
import { escapeMarkup, parseMarkup } from './lib/markup.js';
import { validateFile } from './lib/files.js';
import { linkUrl, safeUrl } from './lib/urls.js';

const props = defineProps({ createUrl: String, siteKey: String, csrfToken: String, sort: String, reload: Function });
defineEmits(['open']);
const form = ref(), textInput = ref(), captcha = ref();
const draft = reactive({ username: '', email: '', homepage: '', text: '' });
const reply = ref(null), quote = ref(null), preview = ref(null), file = ref(null);
const errors = ref({}), status = ref(''), posting = ref(false), linking = ref(false);
const link = reactive({ url: '', title: '', error: '' });
const fields = [['username', 'User Name', 'text', 80], ['email', 'E-mail', 'email', 254], ['homepage', 'Home page', 'url', 2048]];
let selection = [0, 0], widget, captchaScript;

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
    const html = parseMarkup(draft.text);
    if (form.value.reportValidity()) preview.value = { ...draft, rendered_text: html, created_at: new Date().toISOString(), quoted_comment: quote.value };
  } catch (error) { errors.value.text = error.message; }
}

async function insert(markup) {
  const [start, end] = selection;
  draft.text = draft.text.slice(0, start) + markup + draft.text.slice(end);
  preview.value = null;
  await nextTick();
  textInput.value.focus();
  textInput.value.setSelectionRange(start, start + markup.length);
}
function format(tag) {
  selection = [textInput.value.selectionStart, textInput.value.selectionEnd];
  if (tag === 'a') { linking.value = !linking.value; return; }
  const selected = draft.text.slice(...selection) || 'text';
  insert(`<${tag}>${tag === 'code' ? escapeMarkup(selected) : selected}</${tag}>`);
}
function insertLink() {
  try {
    linkUrl(link.url);
    insert(`<a href="${escapeMarkup(link.url)}" title="${escapeMarkup(link.title)}">${draft.text.slice(...selection) || escapeMarkup(link.url)}</a>`);
    linking.value = false;
    link.error = '';
  } catch (error) { link.error = error.message; }
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
  try { parseMarkup(draft.text); }
  catch (error) { errors.value.text = error.message; return; }
  if (!form.value.reportValidity()) return;
  // Lock before async validation as well as the request to prevent double posts.
  posting.value = true;
  let sent = false, saved = false;
  try {
    try { await validateFile(form.value.elements.attachment.files[0]); }
    catch (error) { errors.value.attachment = error.message; return; }
    const data = new FormData(form.value);
    if (!data.get('g-recaptcha-response')) { errors.value.recaptcha = 'Complete the Google reCAPTCHA challenge.'; return; }
    data.set('sort', props.sort);
    status.value = 'Posting comment…';
    sent = true;
    const response = await fetch(safeUrl(props.createUrl), {
      method: 'POST', body: data, headers: { 'X-CSRFToken': props.csrfToken, Accept: 'application/json' },
    });
    saved = response.ok;
    const result = await response.json();
    if (!saved) { errors.value = result.errors || { __all__: 'Your comment could not be posted.' }; status.value = 'Please check your comment.'; return; }
    Object.keys(draft).forEach(key => { draft[key] = ''; });
    form.value.reset();
    reply.value = quote.value = preview.value = file.value = null;
    linking.value = false;
    const url = safeUrl(result.list_url || location.href);
    if (Number.isSafeInteger(result.comment_id)) url.hash = `comment-${result.comment_id}`;
    const refreshed = await props.reload(url);
    status.value = refreshed ? 'Your comment has been posted.' : 'Your comment was posted. Refresh the discussion to see it.';
  } catch {
    status.value = saved ? 'Your comment was posted. Refresh the discussion to see it.' : 'We could not confirm your submission. Check the discussion before trying again.';
  } finally {
    if (sent) window.grecaptcha?.reset(widget);
    posting.value = false;
  }
}

onMounted(() => {
  if (!props.siteKey) return;
  // Vue creates the widget container, so render reCAPTCHA after mounting.
  window.commentsCaptchaReady = () => { widget = window.grecaptcha.render(captcha.value, { sitekey: props.siteKey, size: 'compact' }); };
  captchaScript = document.createElement('script');
  captchaScript.src = 'https://www.google.com/recaptcha/api.js?onload=commentsCaptchaReady&render=explicit';
  captchaScript.async = true;
  document.head.append(captchaScript);
});
onUnmounted(() => { captchaScript?.remove(); delete window.commentsCaptchaReady; });
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
    <label for="id_text">Text *</label>
    <div class="format-toolbar"><button v-for="tag in ['i', 'strong', 'code', 'a']" :key="tag" type="button" :data-format="tag" @click="format(tag)">[{{ tag }}]</button></div>
    <div v-show="linking" class="link-fields">
      <label for="link-url">Link URL</label><input id="link-url" v-model="link.url" type="url" :disabled="!linking">
      <label for="link-title">Link title (optional)</label><input id="link-title" v-model="link.title" :disabled="!linking">
      <button type="button" data-insert-link @click="insertLink">Insert link</button><span class="error">{{ link.error }}</span>
    </div>
    <textarea ref="textInput" id="id_text" v-model="draft.text" name="text" required maxlength="10000" rows="5" aria-describedby="text-errors"></textarea>
    <small>Allowed: a (href, title), code, i, strong. Close every tag; escape literal &amp; and &lt;.</small>
    <p id="text-errors" class="error" role="alert">{{ [].concat(errors.text || []).join(' ') }}</p>
    <label for="id_attachment">Image or text file</label><input id="id_attachment" name="attachment" type="file" accept=".jpg,.jpeg,.gif,.png,.txt" @change="chooseFile">
    <small>JPG, GIF or PNG up to 10 MB, resized to 320 × 240. UTF-8 TXT up to 100 KB.</small>
    <p id="attachment-errors" class="error">{{ [].concat(errors.attachment || []).join(' ') }}</p>
    <button v-if="file" type="button" data-preview-file @click="$emit('open', { upload: file, original_name: file.name, kind: /\.txt$/i.test(file.name) ? 'text' : 'image' })">View selected file</button>
    <div ref="captcha" class="captcha"></div><p v-if="!siteKey">Verification is currently unavailable. Please try again later.</p>
    <p id="recaptcha-errors" class="error">{{ [].concat(errors.recaptcha || []).join(' ') }}</p>
    <input type="hidden" name="csrfmiddlewaretoken" :value="csrfToken"><input type="hidden" name="parent_id" :value="reply?.pk || ''"><input type="hidden" name="quoted_comment_id" :value="quote?.pk || ''">
    <div class="buttons"><button class="primary" data-submit :disabled="posting || !createUrl || !siteKey">Post comment</button><button type="button" data-preview @click="showPreview">Preview</button></div>
    <p data-form-status role="status">{{ status }}</p>
    <section v-if="preview" id="comment-preview"><h3>Preview</h3><CommentCard :comment="preview" :sort="sort" preview /></section>
  </form>
</template>

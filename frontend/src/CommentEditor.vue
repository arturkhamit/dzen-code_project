<script setup>
import { reactive, ref } from 'vue';
import { EditorContent, useEditor } from '@tiptap/vue-3';
import StarterKit from '@tiptap/starter-kit';
import { editorMessage } from './lib/entities.js';
import { linkUrl } from './lib/urls.js';

const emit = defineEmits(['change']);
const linking = ref(false), link = reactive({ url: '', error: '', from: 0, to: 0 });
const formats = [['italic', 'Italic'], ['bold', 'Bold'], ['code', 'Code']];
// Keep selection, undo and keyboard editing in the editor library. Only these
// four marks are serialized into our plain-text + entities API.
const editor = useEditor({
  extensions: [StarterKit.configure({
    blockquote: false, bulletList: false, codeBlock: false, heading: false,
    horizontalRule: false, listItem: false, listKeymap: false, orderedList: false,
    strike: false, underline: false, trailingNode: false,
    link: { autolink: false, linkOnPaste: false, openOnClick: false, HTMLAttributes: { target: null, rel: 'nofollow ugc noopener noreferrer' } },
  })],
  editorProps: {
    attributes: { id: 'id_text', class: 'message-editor', role: 'textbox', 'aria-multiline': 'true', 'aria-required': 'true', 'aria-labelledby': 'text-label', 'aria-describedby': 'text-errors' },
    handlePaste(view, event) {
      // Pasted HTML is text, not active markup; formatting is applied explicitly.
      event.preventDefault();
      const text = event.clipboardData?.getData('text/plain') || '';
      if (text) view.dispatch(view.state.tr.insertText(text.replace(/\r\n?/g, '\n')));
      return true;
    },
  },
  onUpdate: ({ editor }) => emit('change', editorMessage(editor.getJSON())),
});

function openLink() {
  if (!editor.value) return;
  if (editor.value.isActive('link')) editor.value.commands.extendMarkRange('link');
  const { from, to } = editor.value.state.selection;
  Object.assign(link, { from, to, url: editor.value.getAttributes('link').href || '', error: '' });
  linking.value = !linking.value;
}
function insertLink() {
  try {
    linkUrl(link.url);
    if (link.from === link.to) throw new Error('Select the text you want to link first.');
    editor.value.chain().focus().setTextSelection({ from: link.from, to: link.to }).setLink({ href: link.url }).run();
    linking.value = false;
  } catch (error) { link.error = error.message; }
}
defineExpose({
  focus: () => editor.value?.commands.focus(),
  clear: () => { editor.value?.commands.clearContent(); linking.value = false; },
});
</script>

<template>
  <div class="format-toolbar" role="toolbar" aria-label="Text formatting">
    <button v-for="[mark, label] in formats" :key="mark" type="button" :data-format="mark" :aria-pressed="editor?.isActive(mark) || false"
            @mousedown.prevent @click="editor?.chain().focus().toggleMark(mark).run()">{{ label }}</button>
    <button type="button" data-format="link" :aria-pressed="editor?.isActive('link') || false" @mousedown.prevent @click="openLink">Link</button>
    <button type="button" data-clear-format @mousedown.prevent @click="editor?.chain().focus().unsetAllMarks().run()">Clear formatting</button>
  </div>
  <div v-show="linking" class="link-fields">
    <label for="link-url">Link URL</label><input id="link-url" v-model="link.url" type="url" :disabled="!linking" @keydown.enter.prevent="insertLink">
    <button type="button" data-insert-link @click="insertLink">Apply link</button>
    <button type="button" @click="linking = false">Cancel</button><span class="error" role="alert">{{ link.error }}</span>
  </div>
  <EditorContent :editor="editor" />
  <small>Select text to format it. Bold: Ctrl/Cmd+B; italic: Ctrl/Cmd+I. You can also type **bold**, *italic* or `code`.</small>
</template>

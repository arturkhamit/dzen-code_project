import { linkUrl } from './urls.js';

const tags = { bold: 'strong', italic: 'i', code: 'code', text_link: 'a' };
const escape = value => value.replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);

export function editorMessage(document) {
  let text = '';
  const entities = [];
  for (const [index, paragraph] of (document.content || []).entries()) {
    if (index) text += '\n';
    for (const node of paragraph.content || []) {
      const value = node.type === 'hardBreak' ? '\n' : node.text || '';
      const offset = text.length, length = value.trimEnd().length;
      text += value;
      if (!length) continue;
      for (const mark of node.marks || []) {
        const type = mark.type === 'link' ? 'text_link' : mark.type;
        if (!Object.hasOwn(tags, type)) continue;
        entities.push({ type, offset, length, ...(type === 'text_link' ? { url: mark.attrs.href } : {}) });
      }
    }
  }
  // JS string lengths already use Telegram's UTF-16 convention, including emoji.
  return { text, entities };
}

export function renderMessage(text, entities) {
  if (!text.trim() || text.length > 10000 || text.includes('\0')) throw new Error('Enter between 1 and 10,000 characters.');
  const ordered = [...entities].sort((a, b) => a.offset - b.offset || b.length - a.length || a.type.localeCompare(b.type));
  const output = [], stack = [];
  let cursor = 0;
  for (const entity of ordered) {
    while (stack.length && stack.at(-1).end <= entity.offset) {
      const { end, tag } = stack.pop();
      output.push(escape(text.slice(cursor, end)), `</${tag}>`);
      cursor = end;
    }
    const tag = tags[entity.type];
    if (!tag) throw new Error('Unsupported formatting.');
    let attributes = '';
    if (tag === 'a') {
      linkUrl(entity.url);
      attributes = ` href="${escape(entity.url)}" rel="nofollow ugc noopener noreferrer"`;
    }
    output.push(escape(text.slice(cursor, entity.offset)), `<${tag}${attributes}>`);
    cursor = entity.offset;
    stack.push({ end: entity.offset + entity.length, tag });
  }
  while (stack.length) {
    const { end, tag } = stack.pop();
    output.push(escape(text.slice(cursor, end)), `</${tag}>`);
    cursor = end;
  }
  output.push(escape(text.slice(cursor)));
  return output.join('');
}

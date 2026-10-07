<script setup>
import avatar from './avatar.svg';

defineProps({ comment: Object, preview: Boolean, sort: { type: String, default: 'newest' } });
defineEmits(['reply', 'quote', 'open']);
</script>

<template>
  <article class="comment" :id="preview ? undefined : `comment-${comment.pk}`"
           :data-comment-id="preview ? undefined : comment.pk" :style="{ '--depth': comment.depth || 0 }">
    <header class="comment__header">
      <img class="avatar" data-avatar :src="comment.avatar_url || avatar" alt="" width="32" height="32" referrerpolicy="no-referrer">
      <div class="identity">
        <component :is="comment.homepage ? 'a' : 'strong'" data-username :href="comment.homepage || undefined" rel="nofollow ugc noopener noreferrer">{{ comment.username }}</component>
        <time :datetime="comment.created_at">{{ new Date(comment.created_at).toLocaleString() }}</time>
      </div>
      <div v-if="!preview" class="actions">
        <button type="button" data-reply-to :aria-label="`Reply to ${comment.username}`" @click="$emit('reply', comment)">↩</button>
        <button type="button" data-quote :aria-label="`Quote ${comment.username}`" @click="$emit('quote', comment)">❝</button>
        <span class="comment__votes" :aria-label="`${comment.vote_count} votes`">▴ {{ comment.vote_count }}</span>
        <a :href="`#comment-${comment.pk}`" aria-label="Link to comment">#</a>
      </div>
    </header>
    <a v-if="comment.parent_id" class="parent" :href="`#comment-${comment.parent_id}`">↳ Reply to #{{ comment.parent_id }}</a>
    <blockquote v-if="comment.quoted_comment">
      <a :href="`?comment=${comment.quoted_comment.pk}&sort=${encodeURIComponent(sort)}#comment-${comment.quoted_comment.pk}`">
        <strong data-quote-author>{{ comment.quoted_comment.username }}</strong>
        <span class="quote-text">{{ comment.quoted_comment.plain_text }}</span>
      </a>
    </blockquote>
    <!-- Only the server serializer or our XHTML validator may produce rendered_text. -->
    <div class="comment__text" data-comment-text v-html="comment.rendered_text"></div>
    <a v-if="comment.attachment" class="attachment" :href="comment.attachment.file.url" @click.prevent="$emit('open', comment.attachment)">
      <img v-if="comment.attachment.kind === 'image'" :src="comment.attachment.file.url" :alt="comment.attachment.original_name" loading="lazy">
      <span v-else>↗ {{ comment.attachment.original_name }}</span>
    </a>
  </article>
</template>

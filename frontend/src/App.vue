<script setup>
import { nextTick, onMounted, onUnmounted, ref } from 'vue';
import CommentCard from './CommentCard.vue';
import CommentForm from './CommentForm.vue';
import FileViewer from './FileViewer.vue';
import { safeUrl } from './lib/urls.js';

const props = defineProps({ initial: Object, listUrl: String, createUrl: String, siteKey: String, csrfToken: String, sort: String });
const page = ref(props.initial), sort = ref(props.sort || 'newest'), status = ref('');
const composer = ref(), viewer = ref();
const sorts = { newest: 'Newest first', oldest: 'Oldest first', username_asc: 'User Name A–Z', username_desc: 'User Name Z–A', email_asc: 'E-mail A–Z', email_desc: 'E-mail Z–A' };
const columns = [['User Name', 'username_asc', 'username_desc'], ['E-mail', 'email_asc', 'email_desc'], ['Date added', 'oldest', 'newest']];
const link = (number = 1, order = sort.value) => `${props.listUrl}?${new URLSearchParams({ page: number, sort: order })}`;
let request;

async function load(address, push = true) {
  request?.abort();
  const controller = request = new AbortController();
  status.value = 'Loading comments…';
  try {
    const url = safeUrl(address);
    const response = await fetch(url, { signal: controller.signal, headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error('Comments could not be loaded. Please try again.');
    const data = await response.json();
    if (!Array.isArray(data.comments)) throw new Error('The server returned an unexpected comments page.');
    page.value = data;
    sort.value = url.searchParams.get('sort') || 'newest';
    if (push) history.pushState({}, '', url);
    status.value = 'Comments updated.';
    await nextTick();
    if (url.hash) document.getElementById(url.hash.slice(1))?.scrollIntoView({ block: 'center' });
    return true;
  } catch (error) {
    if (error.name !== 'AbortError') status.value = error.message;
    return false;
  }
}
const back = () => load(location.href, false);
window.addEventListener('popstate', back);
onMounted(() => { if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView({ block: 'center' }); });
onUnmounted(() => { window.removeEventListener('popstate', back); request?.abort(); });
</script>

<template>
  <main class="comments-page">
    <header class="heading"><div><small>Community</small><h1>Discussion</h1><p>Share a thought. Join the conversation.</p></div><a href="#comment-form">Write a comment</a></header>
    <p data-list-status role="status">{{ status }}</p>
    <section class="panel" id="comment-results" aria-label="Comments">
      <div class="toolbar">
        <span>{{ page.count }} discussions · 25 per page</span>
        <form data-sort-form @submit.prevent="load(link())">
          <label for="sort">Sort by </label><select id="sort" v-model="sort"><option v-for="(label, value) in sorts" :key="value" :value="value">{{ label }}</option></select>
          <button>Sort</button>
        </form>
      </div>
      <div v-if="page.comments.length" class="comments-table-wrap">
        <table>
          <thead><tr><th v-for="[label, asc, desc] in columns" :key="label" scope="col" :aria-sort="sort === asc ? 'ascending' : sort === desc ? 'descending' : 'none'">
            <a :href="link(1, sort === asc ? desc : asc)" @click.prevent="load(link(1, sort === asc ? desc : asc))">{{ label }} ↕</a>
          </th></tr></thead>
          <tbody v-for="root in page.comments" :key="root.pk">
            <tr class="comments-table__metadata"><th scope="row">{{ root.username }}</th><td>{{ root.email }}</td><td>{{ new Date(root.created_at).toLocaleString() }}</td></tr>
            <tr><td colspan="3"><div class="thread">
              <CommentCard v-for="comment in root.thread" :key="comment.pk" :comment="comment" :sort="sort"
                           @reply="composer.select($event, 'reply')" @quote="composer.select($event, 'quote')" @open="viewer.open($event)" />
            </div></td></tr>
          </tbody>
        </table>
      </div>
      <p v-else class="empty">No comments yet. Start the discussion.</p>
      <nav v-if="page.pages > 1" class="pagination" aria-label="Comment pages">
        <a v-if="page.page > 1" :href="link(page.page - 1)" rel="prev" @click.prevent="load(link(page.page - 1))">← Previous</a>
        <span>Page {{ page.page }} of {{ page.pages }}</span>
        <a v-if="page.page < page.pages" :href="link(page.page + 1)" rel="next" @click.prevent="load(link(page.page + 1))">Next →</a>
      </nav>
    </section>
    <CommentForm ref="composer" :create-url="createUrl" :site-key="siteKey" :csrf-token="csrfToken" :sort="sort" :reload="load" @open="viewer.open($event)" />
    <FileViewer ref="viewer" />
  </main>
</template>

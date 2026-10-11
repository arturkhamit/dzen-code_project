import { reactive } from 'vue';
import { safeUrl } from './urls.js';

export function createAuth(urls, csrfToken) {
  const state = reactive({ user: null, ready: false, busy: false, error: '', csrfToken });
  // Access tokens live only in this closure; Django's HttpOnly cookie renews them.
  let access = '', renewal, version = 0;
  const csrf = () => document.cookie.split('; ').find(value => value.startsWith('csrftoken='))?.slice(10) || state.csrfToken;
  const clear = () => { access = ''; state.user = null; };
  const accept = data => {
    access = data.access_token;
    state.user = data.user;
    state.csrfToken = data.csrf_token;
  };

  function send(url, options = {}, token = access) {
    const headers = new Headers(options.headers);
    headers.set('Accept', 'application/json');
    headers.set('X-CSRFToken', csrf());
    if (token) headers.set('Authorization', `Bearer ${token}`);
    // A stale hidden field takes precedence over the CSRF header in Django.
    if (options.body instanceof FormData) options.body.delete('csrfmiddlewaretoken');
    return fetch(safeUrl(url), { ...options, headers, credentials: 'same-origin' });
  }

  async function result(response) {
    const data = response.status === 204 ? {} : await response.json().catch(() => ({}));
    if (!response.ok) {
      const errors = data.errors || { __all__: ['The request failed. Please try again.'] };
      throw Object.assign(new Error(Object.values(errors).flat().join(' ')), { errors });
    }
    return data;
  }

  function renew() {
    if (!renewal) {
      const started = version;
      renewal = (async () => {
        const response = await send(urls.refresh, { method: 'POST' }, '');
        if (started !== version) throw new Error('Your login changed. Please try again.');
        if (response.status === 401) { clear(); return false; }
        const data = await result(response);
        if (started !== version) throw new Error('Your login changed. Please try again.');
        accept(data);
        return true;
      })().finally(() => { renewal = null; });
    }
    return renewal;
  }

  async function authenticatedFetch(url, options = {}) {
    const response = await send(url, options);
    if (response.status !== 401) return response;
    if (await renew()) return send(url, options);
    state.error = 'Your session expired. Sign in again, or enter your details to post as a guest.';
    // Never retry a failed authenticated submission as an anonymous comment.
    return response;
  }

  async function action(name, data) {
    if (state.busy) return;
    version++;
    state.busy = true;
    state.error = '';
    try {
      const options = { method: name === 'me' ? 'PATCH' : 'POST' };
      if (data) {
        options.headers = { 'Content-Type': 'application/json' };
        options.body = JSON.stringify(data);
      }
      const response = await (['me', 'password'].includes(name)
        ? authenticatedFetch(urls[name], options) : send(urls[name], options, ''));
      const payload = await result(response);
      if (name === 'logout') clear();
      else if (payload.access_token) accept(payload);
      else state.user = payload.user;
      return payload;
    } finally { state.busy = false; }
  }

  async function restore() {
    state.error = '';
    try { await renew(); }
    catch (error) { state.error = error.message; }
    finally { state.ready = true; }
  }

  return { state, action, restore, fetch: authenticatedFetch };
}

<script setup>
import { computed, reactive, ref, watch } from 'vue';

const props = defineProps({ auth: Object });
const mode = ref(''), error = ref(''), status = ref(''), draft = reactive({});
const labels = { login: 'Sign in', register: 'Create account', me: 'Save profile', password: 'Change password' };
const fields = {
  username: ['User Name', 'text', 'username', 80], email: ['E-mail', 'email', 'email', 254],
  homepage: ['Home page (optional)', 'url', 'url', 2048],
  password: ['Password', 'password', 'current-password', 128],
  password1: ['Password', 'password', 'new-password', 128],
  password2: ['Confirm password', 'password', 'new-password', 128],
  old_password: ['Current password', 'password', 'current-password', 128],
  new_password1: ['New password', 'password', 'new-password', 128],
  new_password2: ['Confirm new password', 'password', 'new-password', 128],
};
const visibleFields = computed(() => ({
  login: ['username', 'password'], register: ['username', 'email', 'homepage', 'password1', 'password2'],
  me: ['email', 'homepage'], password: ['old_password', 'new_password1', 'new_password2'],
})[mode.value] || []);

function open(next) {
  Object.keys(draft).forEach(key => delete draft[key]);
  Object.assign(draft, { email: props.auth.state.user?.email || '', homepage: props.auth.state.user?.homepage || '' });
  mode.value = next;
  error.value = status.value = '';
}
watch(() => props.auth.state.user?.id, () => { mode.value = ''; });

async function submit(name = mode.value) {
  if (props.auth.state.busy) return;
  error.value = status.value = '';
  try {
    const data = name === 'logout' ? null : Object.fromEntries(visibleFields.value.map(key => [key, draft[key] || '']));
    await props.auth.action(name, data);
    open('');
    status.value = ({ login: 'Signed in.', register: 'Your account is ready.', me: 'Profile saved.', password: 'Password changed.', logout: 'Signed out.' })[name];
  } catch (failure) { error.value = failure.message; }
}
</script>

<template>
  <section class="panel account-panel" aria-label="Your account">
    <div class="toolbar">
      <span v-if="!auth.state.ready">Checking login…</span>
      <span v-else-if="auth.state.user">Signed in as <strong>{{ auth.state.user.username }}</strong></span>
      <span v-else>Post as a guest, or sign in to use your saved details.</span>
      <div class="account-actions">
        <template v-if="auth.state.user">
          <button type="button" :disabled="auth.state.busy" @click="open('me')">Account</button>
          <button type="button" :disabled="auth.state.busy" @click="open('password')">Change password</button>
          <button type="button" :disabled="auth.state.busy" @click="submit('logout')">Sign out</button>
        </template>
        <template v-else>
          <button type="button" :disabled="!auth.state.ready || auth.state.busy" @click="open('login')">Sign in</button>
          <button type="button" :disabled="!auth.state.ready || auth.state.busy" @click="open('register')">Create account</button>
        </template>
      </div>
    </div>
    <p v-if="auth.state.error" class="error" role="alert">{{ auth.state.error }}</p>
    <p class="error" role="alert">{{ error }}</p>
    <p role="status">{{ status }}</p>
    <form v-if="mode" class="account-form" @submit.prevent="submit()">
      <h2>{{ labels[mode] }}</h2>
      <div class="fields">
        <label v-for="name in visibleFields" :key="name" :for="`account_${name}`">
          {{ fields[name][0] }}
          <input :id="`account_${name}`" v-model="draft[name]" :name="name" :type="fields[name][1]"
                 :autocomplete="fields[name][2]" :maxlength="name === 'username' && mode === 'login' ? 150 : fields[name][3]"
                 :required="name !== 'homepage'" :disabled="auth.state.busy"
                 :pattern="name === 'username' && mode === 'register' ? '[A-Za-z0-9]+' : name === 'homepage' ? 'https?://.+' : undefined">
        </label>
      </div>
      <div class="buttons">
        <button class="primary" :disabled="auth.state.busy">{{ auth.state.busy ? 'Saving…' : labels[mode] }}</button>
        <button type="button" :disabled="auth.state.busy" @click="open('')">Cancel</button>
      </div>
    </form>
  </section>
</template>

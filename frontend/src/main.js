import { createApp } from 'vue';
import App from './App.vue';
import './style.css';

const root = document.querySelector('#comments-app');
createApp(App, {
  ...root.dataset,
  captchaRequired: root.dataset.captchaRequired !== 'false',
  initial: JSON.parse(document.querySelector('#comments-data').textContent),
  authUrls: JSON.parse(document.querySelector('#auth-urls').textContent),
}).mount(root);

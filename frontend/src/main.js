import { createApp } from 'vue';
import App from './App.vue';
import './style.css';

const root = document.querySelector('#comments-app');
createApp(App, { ...root.dataset, initial: JSON.parse(document.querySelector('#comments-data').textContent) }).mount(root);

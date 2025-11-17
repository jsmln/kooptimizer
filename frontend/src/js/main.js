import { API_BASE_URL } from './config.js';

function loginUser(username, password) {
  fetch(`${API_BASE_URL}/api/login`, {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
  .then(response => response.json())
  .then(data => {
    console.log('Login success:', data);
  });
}


if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/service-worker.js')
      .then(registration => {
        console.log('Minimal Service Worker registered successfully.');
      })
      .catch(error => {
        console.log('Service Worker registration failed:', error);
      });
  });
}


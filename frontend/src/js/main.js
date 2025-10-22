// 1. Import the variable at the top of the file
import { API_BASE_URL } from './config.js';

// ... any other code you have ...

// 2. Use the variable in your fetch calls
function loginUser(username, password) {
  
  // --- BEFORE (What you might have now) ---
  // fetch('http://127.0.0.1:8000/api/login', {
  //   method: 'POST',
  //   ...
  // });

  // --- AFTER (Using the config variable) ---
  fetch(`${API_BASE_URL}/api/login`, {
    method: 'POST',
    body: JSON.stringify({ username, password }),
    // ... other options
  })
  .then(response => response.json())
  .then(data => {
    console.log('Login success:', data);
  });
}

// ... rest of your code ...
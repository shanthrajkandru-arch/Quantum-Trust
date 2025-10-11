// frontend/src/index.js

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Import the CSS file from its new location inside the src directory.
import './styles.css'; 

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

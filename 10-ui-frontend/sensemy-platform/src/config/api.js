// src/config/api.js
const API_CONFIG = {
  baseURL: import.meta.env.VITE_TRANSFORM_API_URL || 
           window.APP_CONFIG?.TRANSFORM_API_BASE || 
           'https://api3.sensemy.cloud',
  
  timeout: 10000,
  withCredentials: true,
  
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
};

console.log('🔧 API Configuration loaded:', {
  baseURL: API_CONFIG.baseURL,
  environment: import.meta.env.VITE_NODE_ENV,
  mode: import.meta.env.MODE
});

export default API_CONFIG;

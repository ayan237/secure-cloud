/**
 * SecureCloud Runtime Frontend Configuration
 *
 * This file allows setting a persistent API URL when deployed to Netlify or custom domains.
 * You can also set/change this at runtime via the settings modal in the navigation bar!
 */
window.__SECURECLOUD_CONFIG__ = {
    // Set to your deployed FastAPI backend (e.g. "https://securecloud-api.onrender.com")
    // If left empty (""), it defaults to:
    // - http://127.0.0.1:8000 when opened locally
    // - or your saved URL in browser localStorage
    API_BASE_URL: ""
};

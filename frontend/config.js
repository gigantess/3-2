/**
 * Frontend Configuration
 * Automatically switches between local dev backend and deployed Render backend.
 */
const CONFIG = {
  // If window.API_BASE_URL is set, use it; otherwise auto-detect
  API_BASE_URL: (function() {
    if (window.API_BASE_URL) return window.API_BASE_URL;
    const hostname = window.location.hostname;
    // When running locally
    if (hostname === "localhost" || hostname === "127.0.0.1") {
      // If frontend served directly by FastAPI on port 8000
      if (window.location.port === "8000") {
        return window.location.origin;
      }
      return "http://localhost:8000";
    }
    // Deployed environment: fallback or relative if reverse-proxied
    return window.location.origin;
  })(),
  DEFAULT_STOCK_NAME: "삼성전자 (005930.KS)"
};

console.log("[Config] Loaded API Base URL:", CONFIG.API_BASE_URL);

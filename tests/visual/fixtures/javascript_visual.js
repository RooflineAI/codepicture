// Async data fetcher with retry
async function fetchWithRetry(url, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url);
      return response.json();
    } catch (err) {
      if (i === retries - 1) throw err;
    }
  }
}

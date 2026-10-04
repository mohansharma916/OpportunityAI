/**
 * OpportunityOS — Frontend API Client
 */

// In the browser, use relative URL to route via Next.js rewrites,
// preventing CORS, port mismatch, and macOS localhost/127.0.0.1 resolution errors.
const isServer = typeof window === 'undefined';
const API_BASE = isServer
  ? (process.env.INTERNAL_API_URL || 'http://127.0.0.1:8000')
  : (process.env.NEXT_PUBLIC_API_URL || '');

export async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers: Record<string, string> = { ...(options.headers as any) };
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const errorJson = await res.json();
      message = errorJson.detail || errorJson.message || JSON.stringify(errorJson);
    } catch {
      const errorText = await res.text();
      if (errorText) message = errorText;
    }
    throw new Error(message);
  }

  return res.json();
}

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(
  /\/$/,
  ""
);

export function apiUrl(path: string): string {
  const prefix = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE}${prefix}`;
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(apiUrl(path), {
    ...init,
    headers: { Accept: "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {
      /* ignore */
    }
    const error = new Error(detail) as Error & { status?: number };
    error.status = res.status;
    throw error;
  }
  return res.json() as Promise<T>;
}

export function downloadUrl(path: string): string {
  return apiUrl(path);
}

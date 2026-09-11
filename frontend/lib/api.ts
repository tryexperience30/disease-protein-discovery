import { staticDownload, staticGet } from "@/lib/data";

function trimSlash(value: string): string {
  return value.replace(/\/$/, "");
}

function publicApiBase(): string {
  return trimSlash(process.env.NEXT_PUBLIC_API_URL || "");
}

function serverApiBase(): string {
  const internal = trimSlash(process.env.API_INTERNAL_URL || "");
  if (internal) return internal;
  return publicApiBase();
}

export function isStaticMode(): boolean {
  if (typeof window !== "undefined") {
    return !publicApiBase();
  }
  return !serverApiBase();
}

export function apiUrl(path: string): string {
  const prefix = path.startsWith("/") ? path : `/${path}`;
  const base = typeof window === "undefined" ? serverApiBase() : publicApiBase();
  return `${base}${prefix}`;
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  if (isStaticMode()) {
    return staticGet<T>(path);
  }
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
  if (isStaticMode()) return "#";
  return apiUrl(path);
}

export async function downloadResource(path: string): Promise<void> {
  if (isStaticMode()) {
    await staticDownload(path);
    return;
  }
  const url = apiUrl(path);
  if (typeof window === "undefined") return;
  window.location.href = url;
}

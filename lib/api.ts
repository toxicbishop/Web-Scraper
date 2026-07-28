import axios from "axios";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: BASE });

// Attach token to every request if present
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("scraper_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Auth ──────────────────────────────────────────────────────────────────────
export async function login(username: string, password: string) {
  const { data } = await api.post("/token", { username, password });
  return data.access_token as string;
}

// ── Health ────────────────────────────────────────────────────────────────────
export async function health() {
  const { data } = await api.get("/health");
  return data as { status: string };
}

// ── Scrape ────────────────────────────────────────────────────────────────────
export async function triggerScrape(url: string, use_playwright = false) {
  const { data } = await api.post("/scrape", { url, use_playwright });
  return data as { job_id: number; task_id: string; status: string };
}

export async function getJobStatus(job_id: number) {
  const { data } = await api.get(`/status/${job_id}`);
  return data as {
    job_id: number;
    url: string;
    status: string;
    created_at: string;
    finished_at: string | null;
    error: string | null;
  };
}

// ── Pages ─────────────────────────────────────────────────────────────────────
export async function listPages(skip = 0, limit = 50) {
  const { data } = await api.get("/data", { params: { skip, limit } });
  return data as {
    id: number;
    url: string;
    title: string;
    scraped_at: string;
    content_preview: string;
  }[];
}

export async function getPage(id: number) {
  const { data } = await api.get(`/data/${id}`);
  return data as {
    id: number;
    url: string;
    title: string;
    content: string;
    content_hash: string;
    scraped_at: string;
    last_seen_at: string;
  };
}

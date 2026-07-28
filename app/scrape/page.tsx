"use client";
import { useState } from "react";
import { triggerScrape, getJobStatus } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import StatusBadge from "@/components/StatusBadge";
import Link from "next/link";

export default function ScrapePage() {
  const { token } = useAuthStore();
  const [url, setUrl] = useState("");
  const [usePlaywright, setUsePlaywright] = useState(false);
  const [job, setJob] = useState<Awaited<ReturnType<typeof getJobStatus>> | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleScrape() {
    if (!url.trim()) return;
    setBusy(true);
    setError("");
    try {
      const res = await triggerScrape(url.trim(), usePlaywright);
      const status = await getJobStatus(res.job_id);
      setJob(status);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to queue scrape.");
    } finally {
      setBusy(false);
    }
  }

  async function refresh() {
    if (!job) return;
    setBusy(true);
    try {
      const status = await getJobStatus(job.job_id);
      setJob(status);
    } finally {
      setBusy(false);
    }
  }

  if (!token) {
    return (
      <div className="p-8 max-w-2xl">
        <h1 className="text-xl font-semibold text-white mb-4">Scrape</h1>
        <div className="text-sm text-zinc-500 bg-zinc-900 rounded-lg p-6 text-center">
          Sign in from the <Link href="/auth" className="text-blue-400 hover:text-blue-300">Auth</Link> page first.
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="text-xl font-semibold text-white mb-6">Scrape</h1>

      <div className="bg-zinc-900 rounded-lg p-5 mb-6">
        <label className="text-xs text-zinc-500 mb-1.5 block">URL to scrape</label>
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com"
          className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-zinc-600 mb-3"
        />

        <label className="flex items-center gap-2 text-sm text-zinc-400 mb-4 cursor-pointer">
          <input
            type="checkbox"
            checked={usePlaywright}
            onChange={(e) => setUsePlaywright(e.target.checked)}
            className="rounded"
          />
          Use Playwright (for JS-rendered sites)
        </label>

        {error && <p className="text-sm text-red-400 mb-3">{error}</p>}

        <button
          onClick={handleScrape}
          disabled={busy || !url.trim()}
          className="bg-white text-zinc-950 text-sm font-medium px-4 py-2 rounded-md hover:bg-zinc-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {busy ? "Queuing…" : "Queue scrape"}
        </button>
      </div>

      {job && (
        <div className="bg-zinc-900 rounded-lg p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-medium text-zinc-400">Job #{job.job_id}</h2>
            <StatusBadge status={job.status} />
          </div>
          <p className="text-xs text-zinc-500 mb-1 truncate">{job.url}</p>
          <p className="text-xs text-zinc-600 mb-4">
            Created {new Date(job.created_at).toLocaleTimeString()}
            {job.finished_at && ` · Finished ${new Date(job.finished_at).toLocaleTimeString()}`}
          </p>
          {job.error && (
            <p className="text-xs text-red-400 mb-3">{job.error}</p>
          )}
          <button
            onClick={refresh}
            disabled={busy}
            className="text-xs text-blue-400 hover:text-blue-300 disabled:opacity-50"
          >
            {busy ? "Refreshing…" : "Refresh status ↻"}
          </button>
        </div>
      )}
    </div>
  );
}

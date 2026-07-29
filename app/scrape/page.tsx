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
      setJob(await getJobStatus(res.job_id));
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to queue scrape.");
    } finally {
      setBusy(false);
    }
  }

  async function refresh() {
    if (!job) return;
    setBusy(true);
    try { setJob(await getJobStatus(job.job_id)); }
    finally { setBusy(false); }
  }

  if (!token) {
    return (
      <div className="p-8 max-w-2xl">
        <h1 className="mono text-lg mb-6" style={{ color: "var(--text-primary)" }}>scrape</h1>
        <div className="border rounded-md p-6 text-center text-sm" style={{ borderColor: "var(--border)", background: "var(--panel)", color: "var(--text-secondary)" }}>
          Sign in from <Link href="/auth" className="mono" style={{ color: "var(--info)" }}>/auth</Link> first.
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-2xl">
      <h1 className="mono text-lg mb-1" style={{ color: "var(--text-primary)" }}>scrape</h1>
      <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>Queue a URL for the crawler.</p>

      <div className="border rounded-md p-5 mb-6" style={{ borderColor: "var(--border)", background: "var(--panel)" }}>
        <label className="mono text-[11px] uppercase tracking-wider block mb-2" style={{ color: "var(--text-muted)" }}>
          target url
        </label>
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com"
          className="mono w-full rounded-md px-3 py-2 text-sm mb-3 focus:outline-none"
          style={{ background: "var(--bg)", border: "1px solid var(--border-strong)", color: "var(--text-primary)" }}
        />

        <label className="flex items-center gap-2 text-sm mb-4 cursor-pointer" style={{ color: "var(--text-secondary)" }}>
          <input type="checkbox" checked={usePlaywright} onChange={(e) => setUsePlaywright(e.target.checked)} />
          use playwright (js-rendered sites)
        </label>

        {error && <p className="mono text-[12px] mb-3" style={{ color: "var(--danger)" }}>{error}</p>}

        <button
          onClick={handleScrape}
          disabled={busy || !url.trim()}
          className="mono text-[13px] px-4 py-2 rounded-md transition-opacity disabled:opacity-40"
          style={{ background: "var(--accent)", color: "#1a1305" }}
        >
          {busy ? "queuing…" : "queue scrape →"}
        </button>
      </div>

      {job && (
        <div className="border rounded-md p-5" style={{ borderColor: "var(--border)", background: "var(--panel)" }}>
          <div className="flex items-center justify-between mb-3">
            <p className="mono text-[13px]" style={{ color: "var(--text-primary)" }}>job #{job.job_id}</p>
            <StatusBadge status={job.status} />
          </div>
          <p className="mono text-[11px] mb-1 truncate" style={{ color: "var(--text-muted)" }}>{job.url}</p>
          <p className="mono text-[11px] mb-4" style={{ color: "var(--text-muted)" }}>
            created {new Date(job.created_at).toLocaleTimeString()}
            {job.finished_at && ` · finished ${new Date(job.finished_at).toLocaleTimeString()}`}
          </p>
          {job.error && <p className="mono text-[12px] mb-3" style={{ color: "var(--danger)" }}>{job.error}</p>}
          <button onClick={refresh} disabled={busy} className="mono text-[11px] disabled:opacity-40" style={{ color: "var(--info)" }}>
            {busy ? "refreshing…" : "refresh status →"}
          </button>
        </div>
      )}
    </div>
  );
}

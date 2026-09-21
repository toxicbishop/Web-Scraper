"use client";
import { useEffect, useState } from "react";
import {
  createSchedule, listSchedules, toggleSchedule, deleteSchedule,
  downloadCsv, exportToS3, Schedule, ScrapeMode,
} from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import Link from "next/link";

const modes: ScrapeMode[] = ["static", "playwright", "scroll", "click_through"];

export default function SchedulesPage() {
  const { token } = useAuthStore();
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [url, setUrl] = useState("");
  const [mode, setMode] = useState<ScrapeMode>("static");
  const [minute, setMinute] = useState("*/15");
  const [hour, setHour] = useState("*");
  const [dayOfWeek, setDayOfWeek] = useState("*");
  const [itemSelector, setItemSelector] = useState("");
  const [creating, setCreating] = useState(false);

  const [exporting, setExporting] = useState(false);
  const [exportMsg, setExportMsg] = useState("");

  async function load() {
    setLoading(true);
    try { setSchedules(await listSchedules()); }
    catch { /* ignore */ }
    finally { setLoading(false); }
  }

  useEffect(() => { if (token) load(); }, [token]);

  async function handleCreate() {
    if (!url.trim()) return;
    if (mode === "click_through" && !itemSelector.trim()) {
      setError("item_selector is required for click_through mode");
      return;
    }
    setCreating(true);
    setError("");
    try {
      await createSchedule(url.trim(), {
        mode, minute, hour, day_of_week: dayOfWeek,
        item_selector: itemSelector || undefined,
      });
      setUrl("");
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Failed to create schedule.");
    } finally {
      setCreating(false);
    }
  }

  async function handleToggle(s: Schedule) {
    await toggleSchedule(s.id, !s.enabled);
    await load();
  }

  async function handleDelete(id: number) {
    await deleteSchedule(id);
    await load();
  }

  async function handleCsv() {
    setExporting(true);
    setExportMsg("");
    try {
      await downloadCsv();
      setExportMsg("CSV downloaded.");
    } catch {
      setExportMsg("Export failed.");
    } finally {
      setExporting(false);
    }
  }

  async function handleS3() {
    setExporting(true);
    setExportMsg("");
    try {
      const res = await exportToS3();
      setExportMsg(`Uploaded → ${res.key}`);
    } catch (e: any) {
      setExportMsg(e?.response?.data?.detail || "S3 export failed — check bucket/credentials.");
    } finally {
      setExporting(false);
    }
  }

  if (!token) {
    return (
      <div className="p-8 max-w-3xl">
        <h1 className="mono text-lg mb-6" style={{ color: "var(--text-primary)" }}>schedules</h1>
        <div className="border rounded-md p-6 text-center text-sm" style={{ borderColor: "var(--border)", background: "var(--panel)", color: "var(--text-secondary)" }}>
          Sign in from <Link href="/auth" className="mono" style={{ color: "var(--info)" }}>/auth</Link> first.
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-3xl">
      <h1 className="mono text-lg mb-1" style={{ color: "var(--text-primary)" }}>schedules</h1>
      <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
        Recurring scrapes, driven by Celery Beat. Cron fields use standard crontab syntax.
      </p>

      {/* Create form */}
      <div className="border rounded-md p-5 mb-6" style={{ borderColor: "var(--border)", background: "var(--panel)" }}>
        <label className="mono text-[11px] uppercase tracking-wider block mb-2" style={{ color: "var(--text-muted)" }}>
          target url
        </label>
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com"
          className="mono w-full rounded-md px-3 py-2 text-sm mb-4 focus:outline-none"
          style={{ background: "var(--bg)", border: "1px solid var(--border-strong)", color: "var(--text-primary)" }}
        />

        <label className="mono text-[11px] uppercase tracking-wider block mb-2" style={{ color: "var(--text-muted)" }}>
          mode
        </label>
        <div className="flex gap-2 mb-4 flex-wrap">
          {modes.map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className="mono text-[12px] px-3 py-1.5 rounded-md transition-colors"
              style={{
                border: `1px solid ${mode === m ? "var(--accent)" : "var(--border-strong)"}`,
                color: mode === m ? "var(--accent)" : "var(--text-secondary)",
                background: mode === m ? "var(--accent-dim)" : "transparent",
              }}
            >
              {m}
            </button>
          ))}
        </div>

        {mode === "click_through" && (
          <div className="mb-4">
            <label className="mono text-[11px] uppercase tracking-wider block mb-1.5" style={{ color: "var(--text-muted)" }}>
              item selector
            </label>
            <input
              type="text"
              value={itemSelector}
              onChange={(e) => setItemSelector(e.target.value)}
              placeholder='a[href*="/item/"]'
              className="mono w-full rounded-md px-3 py-2 text-sm focus:outline-none"
              style={{ background: "var(--bg)", border: "1px solid var(--border-strong)", color: "var(--text-primary)" }}
            />
          </div>
        )}

        <label className="mono text-[11px] uppercase tracking-wider block mb-2" style={{ color: "var(--text-muted)" }}>
          cron — minute · hour · day_of_week
        </label>
        <div className="grid grid-cols-3 gap-2 mb-4">
          <input value={minute} onChange={(e) => setMinute(e.target.value)} placeholder="*/15"
            className="mono rounded-md px-3 py-2 text-sm focus:outline-none"
            style={{ background: "var(--bg)", border: "1px solid var(--border-strong)", color: "var(--text-primary)" }} />
          <input value={hour} onChange={(e) => setHour(e.target.value)} placeholder="*"
            className="mono rounded-md px-3 py-2 text-sm focus:outline-none"
            style={{ background: "var(--bg)", border: "1px solid var(--border-strong)", color: "var(--text-primary)" }} />
          <input value={dayOfWeek} onChange={(e) => setDayOfWeek(e.target.value)} placeholder="*"
            className="mono rounded-md px-3 py-2 text-sm focus:outline-none"
            style={{ background: "var(--bg)", border: "1px solid var(--border-strong)", color: "var(--text-primary)" }} />
        </div>
        <p className="mono text-[11px] mb-4" style={{ color: "var(--text-muted)" }}>
          e.g. minute=*/15 → every 15 minutes · hour=9,17 day_of_week=1-5 → 9am &amp; 5pm on weekdays
        </p>

        {error && <p className="mono text-[12px] mb-3" style={{ color: "var(--danger)" }}>{error}</p>}

        <button
          onClick={handleCreate}
          disabled={creating || !url.trim()}
          className="mono text-[13px] px-4 py-2 rounded-md transition-opacity disabled:opacity-40"
          style={{ background: "var(--accent)", color: "#1a1305" }}
        >
          {creating ? "creating…" : "create schedule →"}
        </button>
      </div>

      {/* Export */}
      <div className="border rounded-md p-5 mb-6 flex items-center justify-between flex-wrap gap-3" style={{ borderColor: "var(--border)", background: "var(--panel)" }}>
        <div>
          <p className="mono text-[13px]" style={{ color: "var(--text-primary)" }}>export data</p>
          <p className="text-[12px] mt-0.5" style={{ color: "var(--text-secondary)" }}>
            {exportMsg || "Download all scraped pages, or push to S3."}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleCsv}
            disabled={exporting}
            className="mono text-[12px] px-3 py-1.5 rounded-md disabled:opacity-40"
            style={{ border: "1px solid var(--border-strong)", color: "var(--text-secondary)" }}
          >
            csv →
          </button>
          <button
            onClick={handleS3}
            disabled={exporting}
            className="mono text-[12px] px-3 py-1.5 rounded-md disabled:opacity-40"
            style={{ border: "1px solid var(--border-strong)", color: "var(--text-secondary)" }}
          >
            s3 →
          </button>
        </div>
      </div>

      {/* List */}
      <div className="flex items-center justify-between mb-3">
        <p className="mono text-[11px] uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
          active schedules
        </p>
        <button onClick={load} disabled={loading} className="mono text-[11px] disabled:opacity-40" style={{ color: "var(--info)" }}>
          {loading ? "loading…" : "refresh →"}
        </button>
      </div>

      {!loading && schedules.length === 0 && (
        <div className="border rounded-md p-6 text-center text-sm" style={{ borderColor: "var(--border)", background: "var(--panel)", color: "var(--text-secondary)" }}>
          No schedules yet.
        </div>
      )}

      <div className="flex flex-col gap-2">
        {schedules.map((s) => (
          <div key={s.id} className="border rounded-md px-4 py-3 flex items-center gap-3" style={{ borderColor: "var(--border)", background: "var(--panel)" }}>
            <span
              className="w-1.5 h-1.5 rounded-full flex-shrink-0"
              style={{ background: s.enabled ? "var(--success)" : "var(--text-muted)" }}
            />
            <div className="flex-1 min-w-0">
              <p className="text-sm truncate" style={{ color: "var(--text-primary)" }}>{s.url}</p>
              <p className="mono text-[11px] mt-0.5" style={{ color: "var(--text-muted)" }}>
                [{s.mode}] cron: {s.cron}
                {s.last_triggered_at && ` · last run ${new Date(s.last_triggered_at).toLocaleString()}`}
              </p>
            </div>
            <button
              onClick={() => handleToggle(s)}
              className="mono text-[11px] px-2 py-1 rounded-md flex-shrink-0"
              style={{ border: "1px solid var(--border-strong)", color: "var(--text-secondary)" }}
            >
              {s.enabled ? "pause" : "resume"}
            </button>
            <button
              onClick={() => handleDelete(s.id)}
              className="mono text-[11px] px-2 py-1 rounded-md flex-shrink-0"
              style={{ border: "1px solid var(--border-strong)", color: "var(--danger)" }}
            >
              delete
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

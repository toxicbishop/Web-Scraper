"use client";
import { useEffect, useState } from "react";
import { health, listPages } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import PageRow from "@/components/PageRow";
import PipelineTrace from "@/components/PipelineTrace";
import Link from "next/link";

export default function Dashboard() {
  const { token } = useAuthStore();
  const [online, setOnline] = useState(false);
  const [pages, setPages] = useState<Awaited<ReturnType<typeof listPages>>>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    health().then(() => setOnline(true)).catch(() => setOnline(false));
  }, []);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    listPages(0, 5).then(setPages).catch(() => {}).finally(() => setLoading(false));
  }, [token]);

  return (
    <div className="p-8 max-w-4xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="mono text-lg" style={{ color: "var(--text-primary)" }}>dashboard</h1>
          <p className="text-sm mt-1" style={{ color: "var(--text-secondary)" }}>
            Pipeline status and recent crawl results.
          </p>
        </div>
        <PipelineTrace online={online} />
      </div>

      <div className="grid grid-cols-3 gap-3 mb-8">
        {[
          { label: "pages scraped", value: token ? String(pages.length) : "—" },
          { label: "api", value: online ? "online" : "offline", color: online ? "var(--success)" : "var(--danger)" },
          { label: "auth", value: token ? "authenticated" : "signed out", color: token ? "var(--success)" : "var(--text-muted)" },
        ].map((m) => (
          <div key={m.label} className="border rounded-md p-4" style={{ borderColor: "var(--border)", background: "var(--panel)" }}>
            <p className="mono text-[11px] uppercase tracking-wider mb-1.5" style={{ color: "var(--text-muted)" }}>
              {m.label}
            </p>
            <p className="mono text-lg" style={{ color: m.color ?? "var(--text-primary)" }}>
              {m.value}
            </p>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between mb-3">
        <p className="mono text-[11px] uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
          recent pages
        </p>
        <Link href="/pages" className="mono text-[11px]" style={{ color: "var(--info)" }}>
          view all →
        </Link>
      </div>

      {!token && (
        <div className="border rounded-md p-6 text-center text-sm" style={{ borderColor: "var(--border)", background: "var(--panel)", color: "var(--text-secondary)" }}>
          Sign in from <Link href="/auth" className="mono" style={{ color: "var(--info)" }}>/auth</Link> to see data.
        </div>
      )}

      {token && loading && (
        <p className="mono text-[13px] p-6 text-center" style={{ color: "var(--text-muted)" }}>loading…</p>
      )}

      {token && !loading && pages.length === 0 && (
        <div className="border rounded-md p-6 text-center text-sm" style={{ borderColor: "var(--border)", background: "var(--panel)", color: "var(--text-secondary)" }}>
          No pages scraped yet. Queue one from <Link href="/scrape" className="mono" style={{ color: "var(--info)" }}>/scrape</Link>.
        </div>
      )}

      <div className="flex flex-col gap-2">
        {pages.map((p) => <PageRow key={p.id} {...p} />)}
      </div>
    </div>
  );
}

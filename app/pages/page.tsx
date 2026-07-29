"use client";
import { useEffect, useState } from "react";
import { listPages } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import PageRow from "@/components/PageRow";
import Link from "next/link";

export default function PagesPage() {
  const { token } = useAuthStore();
  const [pages, setPages] = useState<Awaited<ReturnType<typeof listPages>>>([]);
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    try { setPages(await listPages(0, 100)); }
    catch { /* ignore */ }
    finally { setLoading(false); }
  }

  useEffect(() => { if (token) load(); }, [token]);

  if (!token) {
    return (
      <div className="p-8 max-w-3xl">
        <h1 className="mono text-lg mb-6" style={{ color: "var(--text-primary)" }}>pages</h1>
        <div className="border rounded-md p-6 text-center text-sm" style={{ borderColor: "var(--border)", background: "var(--panel)", color: "var(--text-secondary)" }}>
          Sign in from <Link href="/auth" className="mono" style={{ color: "var(--info)" }}>/auth</Link> first.
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="mono text-lg" style={{ color: "var(--text-primary)" }}>pages</h1>
        <button
          onClick={load}
          disabled={loading}
          className="mono text-[11px] px-3 py-1.5 rounded-md disabled:opacity-40"
          style={{ border: "1px solid var(--border-strong)", color: "var(--text-secondary)" }}
        >
          {loading ? "loading…" : "refresh →"}
        </button>
      </div>

      {!loading && pages.length === 0 && (
        <div className="border rounded-md p-6 text-center text-sm" style={{ borderColor: "var(--border)", background: "var(--panel)", color: "var(--text-secondary)" }}>
          No pages scraped yet.
        </div>
      )}

      <div className="flex flex-col gap-2">
        {pages.map((p) => <PageRow key={p.id} {...p} />)}
      </div>
    </div>
  );
}

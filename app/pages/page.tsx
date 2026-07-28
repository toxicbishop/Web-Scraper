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
    try {
      setPages(await listPages(0, 100));
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }

  useEffect(() => {
    if (token) load();
  }, [token]);

  if (!token) {
    return (
      <div className="p-8 max-w-3xl">
        <h1 className="text-xl font-semibold text-white mb-4">Pages</h1>
        <div className="text-sm text-zinc-500 bg-zinc-900 rounded-lg p-6 text-center">
          Sign in from the <Link href="/auth" className="text-blue-400 hover:text-blue-300">Auth</Link> page first.
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-3xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-white">Pages</h1>
        <button
          onClick={load}
          disabled={loading}
          className="text-xs text-zinc-400 hover:text-white border border-zinc-800 rounded-md px-3 py-1.5 disabled:opacity-50"
        >
          {loading ? "Loading…" : "Refresh ↻"}
        </button>
      </div>

      {!loading && pages.length === 0 && (
        <div className="text-sm text-zinc-500 bg-zinc-900 rounded-lg p-6 text-center">
          No pages scraped yet.
        </div>
      )}

      <div className="flex flex-col gap-2">
        {pages.map((p) => (
          <PageRow key={p.id} {...p} />
        ))}
      </div>
    </div>
  );
}

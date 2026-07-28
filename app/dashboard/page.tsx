"use client";
import { useEffect, useState } from "react";
import { health, listPages } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import PageRow from "@/components/PageRow";
import Link from "next/link";

export default function Dashboard() {
  const { token } = useAuthStore();
  const [status, setStatus] = useState<"online" | "offline" | "checking">("checking");
  const [pages, setPages] = useState<Awaited<ReturnType<typeof listPages>>>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    health().then(() => setStatus("online")).catch(() => setStatus("offline"));
  }, []);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    listPages(0, 5)
      .then(setPages)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [token]);

  return (
    <div className="p-8 max-w-4xl">
      <h1 className="text-xl font-semibold text-white mb-6">Dashboard</h1>

      <div className="grid grid-cols-3 gap-3 mb-8">
        <div className="bg-zinc-900 rounded-lg p-4">
          <p className="text-xs text-zinc-500 uppercase tracking-wide mb-1">Pages scraped</p>
          <p className="text-2xl font-semibold text-white">{token ? pages.length : "—"}</p>
        </div>
        <div className="bg-zinc-900 rounded-lg p-4">
          <p className="text-xs text-zinc-500 uppercase tracking-wide mb-1">API status</p>
          <p className={`text-sm font-medium mt-2 flex items-center gap-1.5 ${
            status === "online" ? "text-emerald-400" : status === "offline" ? "text-red-400" : "text-zinc-500"
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${
              status === "online" ? "bg-emerald-400" : status === "offline" ? "bg-red-400" : "bg-zinc-600"
            }`} />
            {status === "checking" ? "Checking…" : status === "online" ? "Online" : "Offline"}
          </p>
        </div>
        <div className="bg-zinc-900 rounded-lg p-4">
          <p className="text-xs text-zinc-500 uppercase tracking-wide mb-1">Auth</p>
          <p className={`text-sm font-medium mt-2 ${token ? "text-emerald-400" : "text-red-400"}`}>
            {token ? "Authenticated" : "Not signed in"}
          </p>
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium text-zinc-400">Recent pages</h2>
          <Link href="/pages" className="text-xs text-blue-400 hover:text-blue-300">View all →</Link>
        </div>

        {!token && (
          <div className="text-sm text-zinc-500 bg-zinc-900 rounded-lg p-6 text-center">
            Sign in from the <Link href="/auth" className="text-blue-400 hover:text-blue-300">Auth</Link> page to see data.
          </div>
        )}

        {token && loading && (
          <div className="text-sm text-zinc-500 p-6 text-center">Loading…</div>
        )}

        {token && !loading && pages.length === 0 && (
          <div className="text-sm text-zinc-500 bg-zinc-900 rounded-lg p-6 text-center">
            No pages scraped yet. Go to <Link href="/scrape" className="text-blue-400 hover:text-blue-300">Scrape</Link> to queue one.
          </div>
        )}

        <div className="flex flex-col gap-2">
          {pages.map((p) => (
            <PageRow key={p.id} {...p} />
          ))}
        </div>
      </div>
    </div>
  );
}

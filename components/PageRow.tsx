"use client";
import { useState } from "react";
import { getPage } from "@/lib/api";

interface Props {
  id: number;
  url: string;
  title: string;
  scraped_at: string;
  content_preview: string;
}

export default function PageRow({ id, url, title, scraped_at, content_preview }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [full, setFull] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function loadFull() {
    if (full) { setExpanded(!expanded); return; }
    setLoading(true);
    try {
      const d = await getPage(id);
      setFull(d.content);
      setExpanded(true);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }

  return (
    <div className="border border-zinc-800 rounded-lg bg-zinc-900 overflow-hidden">
      <div
        className="flex items-start gap-3 px-4 py-3 cursor-pointer hover:bg-zinc-800/50 transition-colors"
        onClick={loadFull}
      >
        <div className="w-2 h-2 rounded-full bg-emerald-400 mt-1.5 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white truncate">{title || "Untitled"}</p>
          <p className="text-xs text-zinc-500 truncate">{url}</p>
        </div>
        <div className="text-xs text-zinc-600 flex-shrink-0">
          {new Date(scraped_at).toLocaleDateString()}
        </div>
        <span className="text-zinc-600 text-xs flex-shrink-0">
          {loading ? "…" : expanded ? "▲" : "▼"}
        </span>
      </div>

      {expanded && (
        <div className="border-t border-zinc-800 px-4 py-3">
          <p className="text-xs text-zinc-400 leading-relaxed whitespace-pre-wrap line-clamp-6">
            {full || content_preview}
          </p>
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-blue-400 hover:text-blue-300 mt-2 inline-block"
          >
            Open original ↗
          </a>
        </div>
      )}
    </div>
  );
}

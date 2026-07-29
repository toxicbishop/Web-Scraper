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
    <div className="border rounded-md overflow-hidden" style={{ borderColor: "var(--border)", background: "var(--panel)" }}>
      <div
        className="flex items-start gap-3 px-4 py-3 cursor-pointer transition-colors hover:brightness-110"
        onClick={loadFull}
      >
        <span className="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0" style={{ background: "var(--success)" }} />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate" style={{ color: "var(--text-primary)" }}>
            {title || "untitled"}
          </p>
          <p className="mono text-[11px] truncate mt-0.5" style={{ color: "var(--text-muted)" }}>
            {url}
          </p>
        </div>
        <span className="mono text-[11px] flex-shrink-0" style={{ color: "var(--text-muted)" }}>
          {new Date(scraped_at).toLocaleDateString()}
        </span>
        <span className="mono text-[11px] flex-shrink-0" style={{ color: "var(--text-muted)" }}>
          {loading ? "..." : expanded ? "−" : "+"}
        </span>
      </div>

      {expanded && (
        <div className="border-t px-4 py-3" style={{ borderColor: "var(--border)" }}>
          <p className="text-[13px] leading-relaxed whitespace-pre-wrap line-clamp-6" style={{ color: "var(--text-secondary)" }}>
            {full || content_preview}
          </p>
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="mono text-[11px] mt-2 inline-block"
            style={{ color: "var(--info)" }}
          >
            open source →
          </a>
        </div>
      )}
    </div>
  );
}

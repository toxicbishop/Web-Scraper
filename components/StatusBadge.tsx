const colors: Record<string, string> = {
  done:    "var(--success)",
  queued:  "var(--text-secondary)",
  running: "var(--accent)",
  failed:  "var(--danger)",
};

export default function StatusBadge({ status }: { status: string }) {
  const c = colors[status] ?? "var(--text-muted)";
  return (
    <span className="mono text-[11px] inline-flex items-center gap-1.5" style={{ color: c }}>
      <span className="w-1.5 h-1.5 rounded-full" style={{ background: c }} />
      [{status}]
    </span>
  );
}

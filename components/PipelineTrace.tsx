const hops = ["client", "api", "worker", "db"];

export default function PipelineTrace({ online }: { online: boolean }) {
  return (
    <div className="flex items-center gap-2">
      {hops.map((hop, i) => (
        <div key={hop} className="flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{ background: online ? "var(--success)" : "var(--danger)" }}
            />
            <span className="mono text-[11px]" style={{ color: "var(--text-secondary)" }}>
              {hop}
            </span>
          </div>
          {i < hops.length - 1 && (
            <span className="mono text-[11px]" style={{ color: "var(--text-muted)" }}>
              →
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

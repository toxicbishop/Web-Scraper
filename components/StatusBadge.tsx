const styles: Record<string, string> = {
  done:    "bg-emerald-950 text-emerald-400 border-emerald-900",
  queued:  "bg-amber-950  text-amber-400  border-amber-900",
  running: "bg-blue-950   text-blue-400   border-blue-900",
  failed:  "bg-red-950    text-red-400    border-red-900",
};

export default function StatusBadge({ status }: { status: string }) {
  const s = styles[status] ?? "bg-zinc-800 text-zinc-400 border-zinc-700";
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${s}`}>
      {status}
    </span>
  );
}

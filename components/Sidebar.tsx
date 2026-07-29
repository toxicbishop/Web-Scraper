"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/lib/store";

const routes = [
  { href: "/dashboard", label: "dashboard" },
  { href: "/scrape",    label: "scrape" },
  { href: "/pages",     label: "pages" },
  { href: "/auth",      label: "auth" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { token, clearToken } = useAuthStore();

  return (
    <aside
      className="w-64 flex flex-col min-h-screen border-r"
      style={{ background: "var(--panel)", borderColor: "var(--border)" }}
    >
      <div className="px-5 py-5 border-b" style={{ borderColor: "var(--border)" }}>
        <p className="mono text-[13px] tracking-tight" style={{ color: "var(--text-primary)" }}>
          web-scraper
        </p>
        <p className="mono text-[11px] mt-0.5" style={{ color: "var(--text-muted)" }}>
          crawl console
        </p>
      </div>

      <nav className="flex-1 py-6 px-5">
        <div className="relative">
          <div className="absolute left-[5px] top-1 bottom-1 trace-line w-px" />
          {routes.map(({ href, label }) => {
            const active = pathname.startsWith(href);
            return (
              <Link key={href} href={href} className="group relative flex items-start gap-3 py-2.5">
                <span
                  className="relative z-10 mt-1.5 w-[11px] h-[11px] flex-shrink-0 border rounded-[2px] transition-colors"
                  style={{
                    background: active ? "var(--accent)" : "var(--panel)",
                    borderColor: active ? "var(--accent)" : "var(--border-strong)",
                  }}
                />
                <div>
                  <p
                    className="mono text-[13px] leading-none transition-colors"
                    style={{ color: active ? "var(--text-primary)" : "var(--text-secondary)" }}
                  >
                    /{label}
                  </p>
                </div>
              </Link>
            );
          })}
        </div>
      </nav>

      <div className="px-5 py-4 border-t" style={{ borderColor: "var(--border)" }}>
        <div className="flex items-center gap-2 mb-3">
          <span
            className="w-1.5 h-1.5 rounded-full"
            style={{ background: token ? "var(--success)" : "var(--danger)" }}
          />
          <p className="mono text-[11px]" style={{ color: "var(--text-secondary)" }}>
            {token ? "authenticated" : "no token"}
          </p>
        </div>
        {token && (
          <button
            onClick={clearToken}
            className="mono text-[11px] transition-colors"
            style={{ color: "var(--text-muted)" }}
          >
            sign out →
          </button>
        )}
      </div>
    </aside>
  );
}

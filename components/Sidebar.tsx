"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/lib/store";

const nav = [
  { href: "/dashboard", label: "Dashboard",  icon: "▦" },
  { href: "/scrape",    label: "Scrape",     icon: "▶" },
  { href: "/pages",     label: "Pages",      icon: "☰" },
  { href: "/auth",      label: "Auth",       icon: "⚿" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { token, clearToken } = useAuthStore();

  return (
    <aside className="w-52 bg-zinc-950 border-r border-zinc-800 flex flex-col min-h-screen">
      <div className="px-5 py-5 flex items-center gap-2 border-b border-zinc-800">
        <span className="text-lg">🕷</span>
        <span className="text-sm font-semibold text-white tracking-tight">Web Scraper</span>
      </div>

      <nav className="flex-1 py-3 flex flex-col gap-0.5 px-2">
        {nav.map(({ href, label, icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                active
                  ? "bg-zinc-800 text-white font-medium"
                  : "text-zinc-400 hover:text-white hover:bg-zinc-900"
              }`}
            >
              <span className="text-base leading-none">{icon}</span>
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="px-4 py-4 border-t border-zinc-800">
        <div className={`text-xs px-2 py-1 rounded-full inline-flex items-center gap-1.5 mb-3 ${
          token ? "bg-emerald-950 text-emerald-400" : "bg-red-950 text-red-400"
        }`}>
          <span className={`w-1.5 h-1.5 rounded-full ${token ? "bg-emerald-400" : "bg-red-400"}`} />
          {token ? "Authenticated" : "No token"}
        </div>
        {token && (
          <button
            onClick={clearToken}
            className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors block"
          >
            Sign out
          </button>
        )}
      </div>
    </aside>
  );
}

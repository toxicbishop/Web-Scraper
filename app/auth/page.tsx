"use client";
import { useState } from "react";
import { login } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import { useRouter } from "next/navigation";

export default function AuthPage() {
  const { token, setToken } = useAuthStore();
  const router = useRouter();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleLogin() {
    setBusy(true);
    setError("");
    try {
      setToken(await login(username, password));
      router.push("/dashboard");
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Login failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="p-8 max-w-sm">
      <h1 className="mono text-lg mb-1" style={{ color: "var(--text-primary)" }}>auth</h1>
      <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>Sign in to access the API.</p>

      <div className="border rounded-md p-5" style={{ borderColor: "var(--border)", background: "var(--panel)" }}>
        <label className="mono text-[11px] uppercase tracking-wider block mb-1.5" style={{ color: "var(--text-muted)" }}>username</label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="mono w-full rounded-md px-3 py-2 text-sm mb-3 focus:outline-none"
          style={{ background: "var(--bg)", border: "1px solid var(--border-strong)", color: "var(--text-primary)" }}
        />

        <label className="mono text-[11px] uppercase tracking-wider block mb-1.5" style={{ color: "var(--text-muted)" }}>password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mono w-full rounded-md px-3 py-2 text-sm mb-4 focus:outline-none"
          style={{ background: "var(--bg)", border: "1px solid var(--border-strong)", color: "var(--text-primary)" }}
        />

        {error && <p className="mono text-[12px] mb-3" style={{ color: "var(--danger)" }}>{error}</p>}

        <button
          onClick={handleLogin}
          disabled={busy}
          className="mono w-full text-[13px] px-4 py-2 rounded-md disabled:opacity-40"
          style={{ background: "var(--accent)", color: "#1a1305" }}
        >
          {busy ? "signing in…" : "sign in →"}
        </button>

        {token && <p className="mono text-[11px] mt-3" style={{ color: "var(--success)" }}>currently signed in</p>}
      </div>

      <p className="mono text-[11px] mt-4" style={{ color: "var(--text-muted)" }}>
        demo credentials: admin / admin
      </p>
    </div>
  );
}

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
      const t = await login(username, password);
      setToken(t);
      router.push("/dashboard");
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Login failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="p-8 max-w-sm">
      <h1 className="text-xl font-semibold text-white mb-6">Auth</h1>

      <div className="bg-zinc-900 rounded-lg p-5">
        <label className="text-xs text-zinc-500 mb-1.5 block">Username</label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-white mb-3 focus:outline-none focus:border-zinc-600"
        />

        <label className="text-xs text-zinc-500 mb-1.5 block">Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-white mb-4 focus:outline-none focus:border-zinc-600"
        />

        {error && <p className="text-sm text-red-400 mb-3">{error}</p>}

        <button
          onClick={handleLogin}
          disabled={busy}
          className="w-full bg-white text-zinc-950 text-sm font-medium px-4 py-2 rounded-md hover:bg-zinc-200 transition-colors disabled:opacity-50"
        >
          {busy ? "Signing in…" : "Sign in"}
        </button>

        {token && (
          <p className="text-xs text-emerald-400 mt-3">Currently signed in.</p>
        )}
      </div>

      <p className="text-xs text-zinc-600 mt-4">
        Default demo credentials: <code className="text-zinc-500">admin / admin</code>
      </p>
    </div>
  );
}

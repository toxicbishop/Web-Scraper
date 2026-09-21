import { create } from "zustand";

interface AuthStore {
  token: string | null;
  setToken: (t: string) => void;
  clearToken: () => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
  token: typeof window !== "undefined" ? localStorage.getItem("scraper_token") : null,
  setToken: (t) => {
    localStorage.setItem("scraper_token", t);
    set({ token: t });
  },
  clearToken: () => {
    localStorage.removeItem("scraper_token");
    set({ token: null });
  },
}));

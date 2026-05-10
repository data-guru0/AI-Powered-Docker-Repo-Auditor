"use client";

import { useRouter } from "next/navigation";
import type { AuthUser } from "@/lib/auth";
import { logoutUser } from "@/lib/auth";
import { useState } from "react";

interface TopBarProps {
  user: AuthUser;
}

export function TopBar({ user }: TopBarProps) {
  const router = useRouter();
  const [loggingOut, setLoggingOut] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  async function handleLogout() {
    setLoggingOut(true);
    try {
      await logoutUser();
      router.push("/login");
    } catch {
      setLoggingOut(false);
    }
  }

  return (
    <header className="h-12 bg-bg-card border-b border-surface-border flex items-center justify-between px-6 shrink-0">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-accent-green animate-pulse-slow" />
          <span className="text-xs text-text-secondary">Live</span>
        </div>
      </div>

      <div className="relative">
        <button
          onClick={() => setMenuOpen((v) => !v)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-bg-hover transition-colors"
        >
          <div className="w-6 h-6 rounded-full bg-accent-purple/20 border border-accent-purple/40 flex items-center justify-center">
            <span className="text-xs font-semibold text-accent-purple">
              {user.email.charAt(0).toUpperCase()}
            </span>
          </div>
          <span className="text-sm text-text-secondary max-w-32 truncate hidden sm:block">
            {user.email}
          </span>
        </button>

        {menuOpen && (
          <div className="absolute right-0 top-full mt-1 w-44 bg-bg-card border border-surface-border rounded-lg shadow-xl py-1 z-50">
            <div className="px-3 py-2 border-b border-surface-border">
              <p className="text-xs text-text-muted truncate">{user.email}</p>
            </div>
            <button
              onClick={handleLogout}
              disabled={loggingOut}
              className="w-full text-left px-3 py-2 text-sm text-text-secondary hover:text-accent-red hover:bg-accent-red/5 transition-colors disabled:opacity-50"
            >
              {loggingOut ? "Signing out..." : "Sign out"}
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

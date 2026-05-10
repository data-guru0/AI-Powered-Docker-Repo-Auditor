"use client";

import { useState, useEffect, useCallback } from "react";
import { getAuthenticatedUser, logoutUser } from "@/lib/auth";
import type { AuthUser } from "@/lib/auth";

export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    setLoading(true);
    const currentUser = await getAuthenticatedUser();
    setUser(currentUser);
    setLoading(false);
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const logout = useCallback(async () => {
    await logoutUser();
    setUser(null);
  }, []);

  return { user, loading, logout, refreshUser };
}

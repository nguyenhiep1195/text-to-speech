"use client";

export function saveAuth(token: string, username: string) {
  localStorage.setItem("tts_token", token);
  localStorage.setItem("tts_user", username);
  // Also set cookie for middleware (no httpOnly so JS can read it)
  document.cookie = `tts_token=${token}; path=/; max-age=${60 * 60 * 8}; SameSite=Lax`;
}

export function clearAuth() {
  localStorage.removeItem("tts_token");
  localStorage.removeItem("tts_user");
  document.cookie = "tts_token=; path=/; max-age=0";
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("tts_token");
}

export function getStoredUser(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("tts_user");
}

export function isAuthenticated(): boolean {
  return !!getStoredToken();
}

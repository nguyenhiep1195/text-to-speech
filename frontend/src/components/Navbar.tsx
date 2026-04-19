"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { clearAuth, getStoredUser, isAuthenticated } from "@/lib/auth";
import { MicVocalIcon, LogOutIcon, LogInIcon, AudioLinesIcon } from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setUser(getStoredUser());
  }, [pathname]);

  const handleLogout = () => {
    clearAuth();
    router.push("/login");
  };

  if (!mounted) return null;

  const loggedIn = isAuthenticated();

  return (
    <nav className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 bg-gradient-to-br from-violet-600 to-indigo-600 rounded-lg flex items-center justify-center shadow-md group-hover:shadow-violet-300 transition-shadow">
              <MicVocalIcon className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-gray-900 text-lg tracking-tight">
              TTS<span className="text-violet-600">Studio</span>
            </span>
          </Link>

          {/* Nav Items */}
          <div className="flex items-center gap-1">
            {loggedIn && (
              <Link
                href="/audio"
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  pathname === "/audio"
                    ? "bg-violet-100 text-violet-700"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`}
              >
                <AudioLinesIcon className="w-4 h-4" />
                Text-to-Speech
              </Link>
            )}
          </div>

          {/* Auth */}
          <div className="flex items-center gap-3">
            {loggedIn ? (
              <>
                <span className="text-sm text-gray-500 hidden sm:block">
                  Xin chào, <span className="font-medium text-gray-700">{user}</span>
                </span>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-red-50 hover:text-red-600 transition-colors border border-gray-200 hover:border-red-200"
                >
                  <LogOutIcon className="w-4 h-4" />
                  Đăng xuất
                </button>
              </>
            ) : (
              <Link
                href="/login"
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-violet-600 text-white hover:bg-violet-700 transition-colors shadow-sm"
              >
                <LogInIcon className="w-4 h-4" />
                Đăng nhập
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}

import Link from "next/link";
import { MicVocalIcon, HomeIcon } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-[calc(100vh-64px)] flex flex-col items-center justify-center px-4 text-center space-y-6">
      <div className="relative">
        <span className="text-[120px] font-black text-gray-100 select-none leading-none">404</span>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-16 h-16 bg-gradient-to-br from-violet-600 to-indigo-600 rounded-2xl flex items-center justify-center shadow-xl">
            <MicVocalIcon className="w-8 h-8 text-white" />
          </div>
        </div>
      </div>

      <div className="space-y-2">
        <h1 className="text-2xl font-bold text-gray-900">Trang không tồn tại</h1>
        <p className="text-gray-500 max-w-sm">
          Trang bạn đang tìm kiếm không tồn tại hoặc đã bị xóa.
        </p>
      </div>

      <div className="flex items-center gap-3">
        <Link
          href="/"
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-violet-600 text-white font-semibold hover:bg-violet-700 transition-colors shadow-sm"
        >
          <HomeIcon className="w-4 h-4" />
          Về trang chủ
        </Link>
        <Link
          href="/audio"
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white text-gray-700 font-semibold hover:bg-gray-100 transition-colors border border-gray-200 shadow-sm"
        >
          Thử TTS
        </Link>
      </div>
    </div>
  );
}

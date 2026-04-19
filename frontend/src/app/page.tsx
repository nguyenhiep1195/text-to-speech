"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated } from "@/lib/auth";
import { MicVocalIcon, AudioLinesIcon, FileTextIcon, DownloadIcon } from "lucide-react";
import Link from "next/link";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated()) {
      router.replace("/audio");
    }
  }, [router]);

  return (
    <div className="min-h-[calc(100vh-64px)] flex flex-col items-center justify-center px-4">
      <div className="max-w-3xl w-full text-center space-y-8">
        {/* Hero */}
        <div className="flex flex-col items-center gap-4">
          <div className="w-20 h-20 bg-gradient-to-br from-violet-600 to-indigo-600 rounded-2xl flex items-center justify-center shadow-xl shadow-violet-200">
            <MicVocalIcon className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-gray-900 tracking-tight">
            TTS<span className="text-violet-600">Studio</span>
          </h1>
          <p className="text-lg text-gray-500 max-w-xl">
            Chuyển đổi văn bản thành giọng nói tự nhiên với nhiều giọng đọc tiếng Việt và tiếng Anh.
            Hỗ trợ tải về file MP3 và phụ đề SRT.
          </p>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-left">
          {[
            {
              icon: <AudioLinesIcon className="w-5 h-5 text-violet-600" />,
              title: "Nhiều giọng đọc",
              desc: "14 giọng đọc tiếng Việt và tiếng Anh với tốc độ và cảm xúc khác nhau",
            },
            {
              icon: <FileTextIcon className="w-5 h-5 text-violet-600" />,
              title: "Văn bản dài",
              desc: "Hỗ trợ văn bản lên đến 500.000 từ với xử lý nền không chặn",
            },
            {
              icon: <DownloadIcon className="w-5 h-5 text-violet-600" />,
              title: "Xuất MP3 & SRT",
              desc: "Tải về file âm thanh MP3 và phụ đề SRT đồng bộ với giọng đọc",
            },
          ].map((f) => (
            <div key={f.title} className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
              <div className="w-9 h-9 bg-violet-50 rounded-lg flex items-center justify-center mb-3">
                {f.icon}
              </div>
              <h3 className="font-semibold text-gray-900 mb-1">{f.title}</h3>
              <p className="text-sm text-gray-500">{f.desc}</p>
            </div>
          ))}
        </div>

        {/* CTA */}
        <Link
          href="/login"
          className="inline-flex items-center gap-2 px-8 py-3 rounded-xl bg-violet-600 text-white font-semibold hover:bg-violet-700 transition-colors shadow-lg shadow-violet-200"
        >
          Bắt đầu ngay
        </Link>
      </div>
    </div>
  );
}

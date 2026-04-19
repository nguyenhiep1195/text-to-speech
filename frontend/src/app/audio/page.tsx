"use client";

import { useState, useEffect } from "react";
import JSZip from "jszip";
import toast from "react-hot-toast";
import {
  AudioLinesIcon,
  SendIcon,
  DownloadIcon,
  FileTextIcon,
  MicIcon,
  RefreshCwIcon,
  CheckCircle2Icon,
  XCircleIcon,
  ClockIcon,
  ChevronDownIcon,
} from "lucide-react";
import { api, Voice, triggerBlobDownload } from "@/lib/api";

type ConvertStatus = "idle" | "converting" | "done" | "error";

const ENGINE_OPTIONS = [
  { value: "edge-tts", label: "Edge TTS (Microsoft)", desc: "Chất lượng cao, có phụ đề SRT" },
  { value: "gtts", label: "Google TTS", desc: "Nhanh hơn, không có SRT" },
];

const SPEED_OPTIONS = [
  { value: 0.5, label: "0.5x – Rất chậm" },
  { value: 0.75, label: "0.75x – Chậm" },
  { value: 1.0, label: "1x – Bình thường" },
  { value: 1.25, label: "1.25x – Nhanh" },
  { value: 1.5, label: "1.5x – Khá nhanh" },
  { value: 1.75, label: "1.75x – Rất nhanh" },
  { value: 2.0, label: "2x – Tốc độ tối đa" },
];

export default function AudioPage() {
  const [text, setText] = useState("");
  const [voice, setVoice] = useState("vi-female");
  const [speed, setSpeed] = useState(1.0);
  const [engine, setEngine] = useState<"edge-tts" | "gtts">("edge-tts");
  const [voices, setVoices] = useState<Voice[]>([]);
  const [loadingVoices, setLoadingVoices] = useState(true);

  const [status, setStatus] = useState<ConvertStatus>("idle");
  const [errorMsg, setErrorMsg] = useState("");

  // Extracted file blobs
  const [mp3Blob, setMp3Blob] = useState<Blob | null>(null);
  const [srtBlob, setSrtBlob] = useState<Blob | null>(null);

  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  const charCount = text.length;

  useEffect(() => {
    api
      .getVoices()
      .then((res) => setVoices(res.voices))
      .catch(() => toast.error("Không thể tải danh sách giọng đọc"))
      .finally(() => setLoadingVoices(false));
  }, []);

  async function handleSubmit() {
    if (!text.trim()) {
      toast.error("Vui lòng nhập nội dung văn bản");
      return;
    }

    setStatus("converting");
    setErrorMsg("");
    setMp3Blob(null);
    setSrtBlob(null);

    try {
      const zipBlob = await api.convertTTS({ text, voice, speed, engine });

      // Extract MP3 and SRT from ZIP
      const zip = await JSZip.loadAsync(zipBlob);

      const mp3File = zip.file("output.mp3");
      const srtFile = zip.file("output.srt");

      if (mp3File) {
        setMp3Blob(new Blob([await mp3File.async("arraybuffer")], { type: "audio/mpeg" }));
      }
      if (srtFile) {
        setSrtBlob(new Blob([await srtFile.async("string")], { type: "text/plain;charset=utf-8" }));
      }

      setStatus("done");
      toast.success("Chuyển đổi hoàn tất!");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Lỗi không xác định";
      setStatus("error");
      setErrorMsg(msg);
      toast.error(msg);
    }
  }

  function handleReset() {
    setStatus("idle");
    setErrorMsg("");
    setMp3Blob(null);
    setSrtBlob(null);
  }

  const isConverting = status === "converting";

  const viVoices = voices.filter((v) => v.lang === "vi");
  const enVoices = voices.filter((v) => v.lang === "en");

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-gradient-to-br from-violet-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-md">
          <AudioLinesIcon className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-gray-900">Text to Speech</h1>
          <p className="text-sm text-gray-500">Chuyển đổi văn bản thành giọng nói</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ── Left: Text Input ─────────────────────────────────────────── */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
            {/* Toolbar */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-gray-50">
              <span className="text-sm font-medium text-gray-700 flex items-center gap-1.5">
                <FileTextIcon className="w-4 h-4 text-gray-400" />
                Nội dung văn bản
              </span>
              <div className="flex items-center gap-3 text-xs text-gray-400">
                <span>{wordCount.toLocaleString()} từ</span>
                <span>{charCount.toLocaleString()} ký tự</span>
                {wordCount > 100_000 && (
                  <span className="text-amber-500 font-medium">⚠ Văn bản rất dài</span>
                )}
              </div>
            </div>

            {/* Textarea */}
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Nhập hoặc dán văn bản vào đây... (hỗ trợ đến 500.000 từ)"
              className="w-full min-h-[400px] p-4 text-sm text-gray-800 placeholder-gray-400 resize-y focus:outline-none font-sans leading-relaxed"
              disabled={isConverting}
            />

            {/* Footer bar */}
            <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 bg-gray-50">
              <button
                onClick={() => { setText(""); handleReset(); }}
                disabled={!text || isConverting}
                className="text-xs text-gray-400 hover:text-red-500 disabled:opacity-40 transition-colors"
              >
                Xóa toàn bộ
              </button>
              <button
                onClick={handleSubmit}
                disabled={isConverting || !text.trim()}
                className="flex items-center gap-2 px-5 py-2 bg-violet-600 hover:bg-violet-700 disabled:bg-violet-400 text-white text-sm font-semibold rounded-lg transition-colors shadow-sm"
              >
                {isConverting ? (
                  <>
                    <Spinner />
                    Đang xử lý...
                  </>
                ) : (
                  <>
                    <SendIcon className="w-4 h-4" />
                    Chuyển đổi
                  </>
                )}
              </button>
            </div>
          </div>

          {/* ── Status / Result ─────────────────────────────────────────── */}
          {status !== "idle" && (
            <div
              className={`rounded-2xl border p-5 space-y-4 ${
                status === "done"
                  ? "bg-green-50 border-green-200"
                  : status === "error"
                  ? "bg-red-50 border-red-200"
                  : "bg-violet-50 border-violet-200"
              }`}
            >
              {/* Status row */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {isConverting && <Spinner className="text-violet-600" />}
                  {status === "done" && <CheckCircle2Icon className="h-5 w-5 text-green-600" />}
                  {status === "error" && <XCircleIcon className="h-5 w-5 text-red-600" />}
                  <span
                    className={`font-semibold text-sm ${
                      status === "done"
                        ? "text-green-700"
                        : status === "error"
                        ? "text-red-700"
                        : "text-violet-700"
                    }`}
                  >
                    {isConverting && "Đang chuyển đổi giọng nói..."}
                    {status === "done" && "Chuyển đổi hoàn tất!"}
                    {status === "error" && "Chuyển đổi thất bại"}
                  </span>
                </div>
                {(status === "done" || status === "error") && (
                  <button
                    onClick={handleReset}
                    className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-700 transition-colors"
                  >
                    <RefreshCwIcon className="w-3.5 h-3.5" />
                    Làm mới
                  </button>
                )}
              </div>

              {/* Processing hint */}
              {isConverting && (
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-xs text-violet-600">
                    <ClockIcon className="w-3.5 h-3.5" />
                    <span>Văn bản dài có thể mất vài phút. Vui lòng đợi...</span>
                  </div>
                  <div className="h-1.5 bg-violet-200 rounded-full overflow-hidden">
                    <div className="h-full bg-violet-500 rounded-full animate-[pulse_1.5s_ease-in-out_infinite] w-2/3" />
                  </div>
                </div>
              )}

              {/* Error */}
              {status === "error" && errorMsg && (
                <p className="text-sm text-red-600 bg-red-100 rounded-lg px-3 py-2">{errorMsg}</p>
              )}

              {/* Download buttons */}
              {status === "done" && (
                <div className="flex flex-wrap gap-3">
                  {mp3Blob && (
                    <button
                      onClick={() => triggerBlobDownload(mp3Blob, "output.mp3")}
                      className="flex items-center gap-2 px-4 py-2.5 bg-green-600 hover:bg-green-700 text-white text-sm font-semibold rounded-lg transition-colors shadow-sm"
                    >
                      <DownloadIcon className="w-4 h-4" />
                      Tải MP3
                    </button>
                  )}
                  {srtBlob && (
                    <button
                      onClick={() => triggerBlobDownload(srtBlob, "output.srt")}
                      className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-lg transition-colors shadow-sm"
                    >
                      <FileTextIcon className="w-4 h-4" />
                      Tải SRT
                    </button>
                  )}
                  {!srtBlob && engine === "edge-tts" && (
                    <span className="text-xs text-gray-400 self-center">
                      SRT không khả dụng cho văn bản này
                    </span>
                  )}
                  {engine === "gtts" && (
                    <span className="text-xs text-amber-500 self-center">
                      Google TTS không hỗ trợ SRT
                    </span>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* ── Right: Settings Panel ────────────────────────────────────── */}
        <div className="space-y-4">
          {/* Engine */}
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-4 space-y-3">
            <h3 className="text-sm font-semibold text-gray-700">Engine</h3>
            <div className="space-y-2">
              {ENGINE_OPTIONS.map((opt) => (
                <label
                  key={opt.value}
                  className={`flex items-start gap-3 p-3 rounded-xl border-2 cursor-pointer transition-all ${
                    engine === opt.value
                      ? "border-violet-500 bg-violet-50"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <input
                    type="radio"
                    name="engine"
                    value={opt.value}
                    checked={engine === opt.value}
                    onChange={() => setEngine(opt.value as "edge-tts" | "gtts")}
                    className="mt-0.5 accent-violet-600"
                    disabled={isConverting}
                  />
                  <div>
                    <div className="text-sm font-medium text-gray-800">{opt.label}</div>
                    <div className="text-xs text-gray-400">{opt.desc}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Voice */}
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-4 space-y-3">
            <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-1.5">
              <MicIcon className="w-4 h-4 text-gray-400" />
              Giọng đọc
            </h3>
            {loadingVoices ? (
              <div className="h-10 bg-gray-100 rounded-lg animate-pulse" />
            ) : (
              <div className="relative">
                <select
                  value={voice}
                  onChange={(e) => setVoice(e.target.value)}
                  disabled={isConverting}
                  className="w-full appearance-none pl-3 pr-8 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 bg-white text-gray-800 disabled:bg-gray-50"
                >
                  {viVoices.length > 0 && (
                    <optgroup label="🇻🇳 Tiếng Việt">
                      {viVoices.map((v) => (
                        <option key={v.id} value={v.id}>
                          {v.gender === "female" ? "♀" : "♂"} {v.name}
                        </option>
                      ))}
                    </optgroup>
                  )}
                  {enVoices.length > 0 && (
                    <optgroup label="🇺🇸 English">
                      {enVoices.map((v) => (
                        <option key={v.id} value={v.id}>
                          {v.gender === "female" ? "♀" : "♂"} {v.name}
                        </option>
                      ))}
                    </optgroup>
                  )}
                </select>
                <ChevronDownIcon className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              </div>
            )}
            {voices.find((v) => v.id === voice) && (
              <p className="text-xs text-gray-400">
                Giọng:{" "}
                <span className="font-mono">{voices.find((v) => v.id === voice)?.voice}</span>
              </p>
            )}
          </div>

          {/* Speed */}
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-4 space-y-3">
            <h3 className="text-sm font-semibold text-gray-700">Tốc độ đọc</h3>
            <div className="relative">
              <select
                value={speed}
                onChange={(e) => setSpeed(parseFloat(e.target.value))}
                disabled={isConverting || engine === "edge-tts"}
                className="w-full appearance-none pl-3 pr-8 py-2.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 bg-white text-gray-800 disabled:bg-gray-50 disabled:text-gray-400"
              >
                {SPEED_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
              <ChevronDownIcon className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>
            {engine === "edge-tts" && (
              <p className="text-xs text-amber-500">
                ℹ Tốc độ được điều chỉnh qua preset giọng đọc với Edge TTS
              </p>
            )}
          </div>

          {/* Info */}
          <div className="bg-violet-50 rounded-2xl border border-violet-200 p-4 space-y-2 text-xs text-violet-700">
            <p className="font-semibold">Lưu ý</p>
            <ul className="space-y-1 text-violet-600 list-disc list-inside">
              <li>Edge TTS: chất lượng cao, có SRT</li>
              <li>Google TTS: nhanh hơn, không có SRT</li>
              <li>Văn bản &gt;100k từ có thể mất vài phút</li>
              <li>Kết quả tự động tải khi hoàn tất</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

function Spinner({ className = "" }: { className?: string }) {
  return (
    <svg
      className={`animate-spin h-4 w-4 ${className}`}
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}

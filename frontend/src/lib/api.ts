const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("tts_token");
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (res.status === 401) {
    if (typeof window !== "undefined") {
      localStorage.removeItem("tts_token");
      localStorage.removeItem("tts_user");
      window.location.href = "/login";
    }
    throw new Error("Phiên đăng nhập hết hạn");
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Lỗi không xác định" }));
    throw new Error(err.detail || "Lỗi không xác định");
  }

  return res.json() as Promise<T>;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  username: string;
}

export interface Voice {
  id: string;
  name: string;
  voice: string;
  gender: string;
  lang: string;
  rate: string;
  pitch: string;
}

export interface JobResponse {
  job_id: string;
  status: "pending" | "processing" | "done" | "error";
  message?: string;
  has_mp3: boolean;
  has_srt: boolean;
}

export interface TTSRequest {
  text: string;
  voice: string;
  speed: number;
  engine: "edge-tts" | "gtts";
  words_per_cue?: number;
}

export const api = {
  login: (username: string, password: string) =>
    request<LoginResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  getVoices: () =>
    request<{ voices: Voice[] }>("/api/voices"),

  /** Synchronous convert → returns ZIP blob (Vercel-compatible) */
  convertTTS: async (data: TTSRequest): Promise<Blob> => {
    const token = getToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(`${API_URL}/api/tts/convert`, {
      method: "POST",
      headers,
      body: JSON.stringify(data),
    });

    if (res.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("tts_token");
        localStorage.removeItem("tts_user");
        window.location.href = "/login";
      }
      throw new Error("Phiên đăng nhập hết hạn");
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Lỗi không xác định" }));
      throw new Error(err.detail || "Lỗi không xác định");
    }

    return res.blob();
  },

  /** Job-based (local dev) */
  createTTSJob: (data: TTSRequest) =>
    request<JobResponse>("/api/tts", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getJobStatus: (jobId: string) =>
    request<JobResponse>(`/api/tts/${jobId}`),
};

export function triggerBlobDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 10_000);
}

export async function downloadFile(
  jobId: string,
  type: "mp3" | "srt",
  filename: string
) {
  const token = getToken();
  const res = await fetch(`${API_URL}/api/tts/${jobId}/download/${type}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error("Tải file thất bại");
  triggerBlobDownload(await res.blob(), filename);
}

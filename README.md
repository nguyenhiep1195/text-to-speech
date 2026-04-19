# TTS Studio – Text to Speech Web App

Ứng dụng web chuyển đổi văn bản thành giọng nói với backend Python FastAPI và frontend Next.js.

## Cấu trúc dự án (Monorepo)

```
text-to-speech/
├── backend/                    # FastAPI Python backend
│   ├── api/
│   │   └── index.py            # Vercel serverless entry point
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── auth.py
│   │   ├── models.py
│   │   └── routes/
│   │       ├── auth_routes.py  # POST /api/auth/login
│   │       └── tts_routes.py   # TTS endpoints
│   ├── src/                    # TTS engine (copy của root src/ – cho Vercel)
│   ├── requirements.txt
│   ├── vercel.json
│   ├── .env                    # Credentials (không commit)
│   ├── .env.example
│   └── run.py
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx        # Trang chủ
│   │   │   ├── login/          # Trang đăng nhập
│   │   │   ├── audio/          # Trang chuyển đổi TTS
│   │   │   └── not-found.tsx
│   │   ├── components/
│   │   │   └── Navbar.tsx
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   └── auth.ts
│   │   └── proxy.ts            # Route protection (Next.js 16)
│   ├── vercel.json
│   ├── .env.local              # Local dev
│   ├── .env.example
│   └── package.json
└── src/                        # TTS engine gốc (dùng cho CLI & local dev)
```

---

## Chạy local

### Backend

```bash
# Dùng virtual environment có sẵn
.venv/bin/pip install -r backend/requirements.txt

cd backend
../.venv/bin/python run.py
# → http://localhost:8000
# → Docs: http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

**Tài khoản mặc định** (trong `backend/.env`):
- Username: `admin` | Password: `admin123`

---

## Deploy lên Vercel

Tạo **2 Vercel project** riêng biệt từ cùng repository.

### Bước 1 – Deploy Backend

1. Vào [vercel.com](https://vercel.com) → **Add New Project** → Import repository này
2. **Root Directory**: `backend`
3. **Framework Preset**: Other
4. Thêm **Environment Variables** trong Vercel dashboard:

   | Key | Value |
   |-----|-------|
   | `TTS_USERNAME` | `admin` |
   | `TTS_PASSWORD` | _(mật khẩu mạnh)_ |
   | `SECRET_KEY` | _(chuỗi ngẫu nhiên 32 ký tự)_ |
   | `CORS_ORIGINS` | `https://your-frontend.vercel.app` |

5. **Deploy** → ghi lại URL, ví dụ: `https://tts-backend-xxx.vercel.app`

> **Lưu ý**: Vercel Hobby plan cho phép function chạy tối đa **60 giây**.  
> Với văn bản dài, nâng lên Pro plan để được **300 giây** (`maxDuration` đã cấu hình sẵn).

---

### Bước 2 – Deploy Frontend

1. **Add New Project** → Import lại cùng repository
2. **Root Directory**: `frontend`
3. **Framework Preset**: Next.js (tự động detect)
4. Thêm **Environment Variables**:

   | Key | Value |
   |-----|-------|
   | `NEXT_PUBLIC_API_URL` | `https://tts-backend-xxx.vercel.app` |

5. **Deploy**

---

### Bước 3 – Cập nhật CORS

Sau khi frontend deploy xong, cập nhật env var `CORS_ORIGINS` ở backend project:

```
CORS_ORIGINS=https://your-frontend-xxx.vercel.app
```

Redeploy backend để áp dụng.

---

## API Endpoints

| Method | Path | Mô tả |
|--------|------|-------|
| POST | `/api/auth/login` | Đăng nhập, nhận JWT |
| GET | `/api/voices` | Danh sách giọng đọc |
| **POST** | **`/api/tts/convert`** | **Chuyển đổi TTS đồng bộ → ZIP (dùng cho Vercel)** |
| POST | `/api/tts` | Tạo job chuyển đổi TTS (local dev) |
| GET | `/api/tts/{job_id}` | Kiểm tra trạng thái job |
| GET | `/api/tts/{job_id}/download/mp3` | Tải file MP3 |
| GET | `/api/tts/{job_id}/download/srt` | Tải file SRT |

### Endpoint chính cho production: `POST /api/tts/convert`

- Nhận: `{text, voice, speed, engine, words_per_cue}`
- Trả về: `application/zip` chứa `output.mp3` và `output.srt`
- Frontend tự động giải nén bằng JSZip và cung cấp nút tải từng file

---

## Giọng đọc hỗ trợ

| Preset | Mô tả |
|--------|-------|
| `vi-female` | Nữ · giọng chuẩn |
| `vi-female-slow` | Nữ · chậm rãi, rõ ràng |
| `vi-female-story` | Nữ · đọc truyện, ấm áp |
| `vi-male` | Nam · giọng chuẩn |
| `vi-male-deep` | Nam · trầm ấm |
| `vi-male-story` | Nam · đọc truyện, trầm lắng |
| `en-female` | English female |
| `en-male` | English male |
| ... | _(14 giọng tổng cộng)_ |

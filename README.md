# TTS Studio – Text to Speech Web App

Ứng dụng web chuyển đổi văn bản thành giọng nói với backend Python FastAPI và frontend VueJS 3.

## Cấu trúc dự án (Monorepo)

```
my-tools/
├── backend/                     # FastAPI Python backend
│   ├── api/
│   │   └── index.py             # Vercel serverless entry point
│   ├── app/
│   │   ├── main.py              # FastAPI app factory
│   │   ├── config.py            # Environment config
│   │   └── routes/
│   │       ├── tts_routes.py    # TTS endpoints
│   │       └── health.py        # Health check
│   ├── src/                     # TTS engine (copy of root src/)
│   ├── requirements.txt
│   ├── vercel.json
│   ├── Dockerfile
│   └── .env.example
├── frontend/                    # VueJS 3 + Vite frontend
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.js
│   │   ├── components/
│   │   │   ├── TextInput.vue
│   │   │   ├── LanguageSelect.vue
│   │   │   ├── VoiceList.vue
│   │   │   ├── VoiceSliders.vue
│   │   │   └── AudioPlayer.vue
│   │   └── composables/
│   │       └── useTTS.js
│   ├── vercel.json
│   ├── Dockerfile
│   ├── nginx.conf
│   └── .env.example
├── docker-compose.yml           # Docker multi-service setup
├── src/                         # TTS engine gốc (dùng cho CLI)
├── main.py                      # CLI entry point
└── requirements.txt             # CLI dependencies
```

---

## Chạy local

### Backend

```bash
cd backend
pip install -r requirements.txt
python run.py
# → http://localhost:8000
# → Docs: http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### Docker (cả 2 services)

```bash
docker-compose up --build
# → Frontend: http://localhost:3000
# → Backend:  http://localhost:8000
```

---

## Deploy lên Vercel

Tạo **2 Vercel project** riêng biệt từ cùng repository.

### Bước 1 – Deploy Backend

1. Vào [vercel.com](https://vercel.com) → **Add New Project** → Import repository
2. **Root Directory**: `backend`
3. **Framework Preset**: Other
4. Thêm **Environment Variables**:

   | Key               | Value                              |
   | ----------------- | ---------------------------------- |
   | `CORS_ORIGINS`    | `https://your-frontend.vercel.app` |
   | `MAX_TEXT_LENGTH` | `5000`                             |

5. **Deploy** → ghi lại URL, ví dụ: `https://tts-backend-xxx.vercel.app`

> **Lưu ý**: Vercel Hobby plan cho phép function chạy tối đa **60 giây**.
> Với văn bản dài, nâng lên Pro plan để được **300 giây**.

### Bước 2 – Deploy Frontend

1. **Add New Project** → Import lại cùng repository
2. **Root Directory**: `frontend`
3. **Framework Preset**: Vite
4. Thêm **Environment Variables**:

   | Key            | Value                                |
   | -------------- | ------------------------------------ |
   | `VITE_API_URL` | `https://tts-backend-xxx.vercel.app` |

5. **Deploy**

### Bước 3 – Cập nhật CORS

Sau khi frontend deploy xong, cập nhật env var `CORS_ORIGINS` ở backend project:

```
CORS_ORIGINS=https://your-frontend-xxx.vercel.app
```

Redeploy backend để áp dụng.

---

## API Endpoints

| Method   | Path                   | Mô tả                                |
| -------- | ---------------------- | ------------------------------------ |
| GET      | `/api/health`          | Health check                         |
| GET      | `/api/voices`          | Danh sách giọng đọc + engines        |
| **POST** | **`/api/tts/convert`** | **Chuyển đổi TTS → ZIP (mp3 + srt)** |

### POST `/api/tts/convert`

**Request Body:**

```json
{
  "text": "Xin chào thế giới",
  "voice": "vi-female",
  "speed": 1.0,
  "pitch": "+0Hz",
  "engine": "edge-tts",
  "generate_srt": false,
  "words_per_cue": 8
}
```

**Response:** `application/zip` chứa `output.mp3` và `output.srt` (nếu `generate_srt=true`).

---

## Giọng đọc hỗ trợ

| Preset            | Mô tả                       |
| ----------------- | --------------------------- |
| `vi-female`       | Nữ · giọng chuẩn            |
| `vi-female-slow`  | Nữ · chậm rãi, rõ ràng      |
| `vi-female-story` | Nữ · đọc truyện, ấm áp      |
| `vi-male`         | Nam · giọng chuẩn           |
| `vi-male-deep`    | Nam · trầm ấm               |
| `vi-male-story`   | Nam · đọc truyện, trầm lắng |
| `en-female`       | English female              |
| `en-male`         | English male                |
| ...               | _(14 giọng tổng cộng)_      |

---

## CLI (vẫn hoạt động)

```bash
python main.py --input sample.txt --voice vi-female-story --srt
python main.py --list-voices
```

Xem thêm: [GUIDE.md](GUIDE.md)

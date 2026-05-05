# Deploy lên Vercel

Monorepo này cần tạo **2 Vercel project** riêng biệt: 1 cho backend, 1 cho frontend.

---

## Bước 1 — Push code lên GitHub

```bash
cd my-tools
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/<your-user>/tts-studio.git
git push -u origin main
```

> **Quan trọng**: Kiểm tra `.gitignore` đã bao gồm `.env` để không push API keys.

---

## Bước 2 — Deploy Backend

1. Vào [vercel.com](https://vercel.com) → **Add New Project** → Import repository
2. Cấu hình:

   | Setting              | Value          |
   | -------------------- | -------------- |
   | **Root Directory**   | `backend`      |
   | **Framework Preset** | `Other`        |
   | **Build Command**    | _(để trống)_   |
   | **Output Directory** | _(để trống)_   |

3. Thêm **Environment Variables**:

   | Key               | Value                                    | Note                          |
   | ----------------- | ---------------------------------------- | ----------------------------- |
   | `CORS_ORIGINS`    | `https://your-frontend-xxx.vercel.app`   | Cập nhật sau khi deploy FE    |
   | `MAX_TEXT_LENGTH`  | `5000`                                   | Giới hạn ký tự                |
   | `GEMINI_API_KEY`   | `AIzaSy...`                              | Optional — cho AI SSML        |
   | `OPENAI_API_KEY`   | `sk-...`                                 | Optional — cho AI SSML        |

4. Click **Deploy**
5. Ghi lại URL backend, ví dụ: `https://tts-backend-xxx.vercel.app`
6. Kiểm tra: `https://tts-backend-xxx.vercel.app/api/health`

> **Lưu ý**: Hobby plan = max 60s function timeout. Văn bản dài cần Pro plan (300s).

---

## Bước 3 — Deploy Frontend

1. **Add New Project** → Import lại **cùng repository**
2. Cấu hình:

   | Setting              | Value        |
   | -------------------- | ------------ |
   | **Root Directory**   | `frontend`   |
   | **Framework Preset** | `Vite`       |
   | **Build Command**    | `npm run build` |
   | **Output Directory** | `dist`       |

3. Thêm **Environment Variables**:

   | Key            | Value                                    |
   | -------------- | ---------------------------------------- |
   | `VITE_API_URL` | `https://tts-backend-xxx.vercel.app`     |

   > `VITE_` prefix bắt buộc — Vite chỉ expose env vars có prefix này.

4. Click **Deploy**
5. Ghi lại URL frontend: `https://tts-frontend-xxx.vercel.app`

---

## Bước 4 — Cập nhật CORS cho Backend

Quay lại **backend project** trên Vercel:

1. **Settings** → **Environment Variables**
2. Sửa `CORS_ORIGINS` thành URL frontend thực tế:

   ```
   CORS_ORIGINS=https://tts-frontend-xxx.vercel.app
   ```

   Nếu có nhiều domain (custom domain + vercel domain):

   ```
   CORS_ORIGINS=https://tts-frontend-xxx.vercel.app,https://yourdomain.com
   ```

3. **Redeploy** backend để áp dụng

---

## Bước 5 — Verify

- Frontend: `https://tts-frontend-xxx.vercel.app` → chọn voice → convert
- Backend health: `https://tts-backend-xxx.vercel.app/api/health`
- Backend voices: `https://tts-backend-xxx.vercel.app/api/voices`

---

## Cấu trúc env tổng hợp

### Backend (`backend/` project)

| Variable          | Required | Default                              | Mô tả                     |
| ----------------- | -------- | ------------------------------------ | -------------------------- |
| `CORS_ORIGINS`    | Yes      | `http://localhost:5173,...:3000`      | Frontend URLs (phân cách `,`) |
| `MAX_TEXT_LENGTH`  | No       | `5000`                               | Giới hạn ký tự input       |
| `GEMINI_API_KEY`   | No       | —                                    | Google Gemini cho SSML      |
| `OPENAI_API_KEY`   | No       | —                                    | OpenAI cho SSML             |

### Frontend (`frontend/` project)

| Variable       | Required | Default | Mô tả                          |
| -------------- | -------- | ------- | ------------------------------- |
| `VITE_API_URL` | Yes      | `""`    | Backend URL (bắt buộc cho prod) |

---

## Troubleshooting

| Vấn đề                              | Giải pháp                                                   |
| ------------------------------------ | ----------------------------------------------------------- |
| CORS error trên browser             | Kiểm tra `CORS_ORIGINS` trên backend có đúng frontend URL   |
| 404 khi gọi `/api/...`              | Kiểm tra backend `vercel.json` routes, redeploy              |
| Frontend trắng, không load          | Kiểm tra `VITE_API_URL` có đúng backend URL không           |
| Function timeout                    | Giảm text length hoặc nâng Pro plan                         |
| `VITE_API_URL` không nhận           | Rebuild frontend sau khi set env (env bake vào build time)   |
| Module not found trên Vercel        | Kiểm tra `requirements.txt` trong `backend/`                |

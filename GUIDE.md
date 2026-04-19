# Hướng dẫn sử dụng — Text-to-Speech CLI

## Mục lục

1. [Cài đặt](#1-cài-đặt)
2. [Cấu trúc thư mục](#2-cấu-trúc-thư-mục)
3. [Chạy nhanh](#3-chạy-nhanh)
4. [Chọn engine TTS](#4-chọn-engine-tts)
5. [Các preset giọng đọc (edge-tts)](#5-các-preset-giọng-đọc-edge-tts)
6. [Tùy chỉnh tốc độ và cao độ](#6-tùy-chỉnh-tốc-độ-và-cao-độ)
7. [Tạo phụ đề SRT](#7-tạo-phụ-đề-srt)
8. [Toàn bộ tùy chọn CLI](#8-toàn-bộ-tùy-chọn-cli)
9. [So sánh các engine](#9-so-sánh-các-engine)
10. [Cài đặt Kokoro (offline)](#10-cài-đặt-kokoro-offline)
11. [Xử lý lỗi thường gặp](#11-xử-lý-lỗi-thường-gặp)

---

## 1. Cài đặt

### Yêu cầu

- Python **3.10+**
- Kết nối internet (cho `edge-tts` và `gtts`; `kokoro` chỉ cần khi tải model lần đầu)

### Bước 1 — Tạo môi trường ảo

```bash
python3 -m venv .venv
source .venv/bin/activate       # macOS / Linux
# .venv\Scripts\activate        # Windows
```

### Bước 2 — Cài thư viện

```bash
# Cài tối thiểu (edge-tts)
pip install edge-tts

# Cài thêm Google TTS
pip install gTTS

# Cài thêm Kokoro (offline, ~82 MB model tải lần đầu)
pip install kokoro soundfile
```

---

## 2. Cấu trúc thư mục

```
text-to-speech/
├── main.py               ← Entry point CLI
├── requirements.txt
├── GUIDE.md              ← File này
├── public/               ← Đặt file .txt đầu vào tại đây
│   └── sample.txt
├── output/               ← File âm thanh và SRT được lưu tại đây
└── src/
    ├── engines/
    │   ├── __init__.py   ← Registry engine
    │   ├── base.py       ← Abstract base class
    │   ├── edge.py       ← edge-tts engine
    │   ├── gtts_engine.py← gTTS engine
    │   └── kokoro_engine.py ← Kokoro engine
    ├── tts.py            ← Facade + VOICE_PRESETS
    ├── srt.py            ← Tạo file SRT
    ├── utils.py          ← Đọc file, chunking, encoding
    └── cli.py            ← Xử lý tham số dòng lệnh
```

---

## 3. Chạy nhanh

```bash
# Chuyển đổi cơ bản (mặc định: edge-tts, giọng nữ chuẩn)
python main.py --input public/sample.txt

# Kết quả: output/sample.mp3
```

---

## 4. Chọn engine TTS

Dùng `--engine` để chọn engine. Có 3 lựa chọn:

```bash
# edge-tts (mặc định) — Microsoft Edge, giọng neural tự nhiên
python main.py --input public/sample.txt --engine edge-tts

# gTTS — Google TTS, hỗ trợ tiếng Việt rất tốt
python main.py --input public/sample.txt --engine gtts

# Kokoro — chạy offline, không cần internet (chỉ tiếng Anh)
python main.py --input public/story_en.txt --engine kokoro --lang en
```

Với `gtts` và `kokoro`, dùng `--lang` để chỉ định ngôn ngữ:

```bash
python main.py --input public/sample.txt --engine gtts --lang vi     # tiếng Việt
python main.py --input public/sample.txt --engine gtts --lang en     # tiếng Anh
python main.py --input public/sample.txt --engine gtts --lang ja     # tiếng Nhật
```

---

## 5. Các preset giọng đọc (edge-tts)

Xem toàn bộ preset:

```bash
python main.py --list-voices
```

### Giọng nữ tiếng Việt

| Preset | Mô tả |
|---|---|
| `vi-female` | Giọng chuẩn |
| `vi-female-slow` | Chậm rãi, rõ ràng |
| `vi-female-gentle` | Nhẹ nhàng, cao giọng |
| `vi-female-news` | Giọng đọc tin tức |
| `vi-female-fast` | Nhanh |
| `vi-female-story` | **Đọc truyện**, ấm áp, tình cảm |
| `vi-female-story-warm` | **Đọc truyện**, chậm rãi, sâu lắng |

### Giọng nam tiếng Việt

| Preset | Mô tả |
|---|---|
| `vi-male` | Giọng chuẩn |
| `vi-male-deep` | Trầm ấm |
| `vi-male-narrator` | Thuyết minh |
| `vi-male-fast` | Nhanh |
| `vi-male-story` | **Đọc truyện**, trầm lắng, cuốn hút |
| `vi-male-story-epic` | **Đọc truyện sử thi**, rất trầm hùng |

```bash
python main.py --input public/truyen.txt --voice vi-female-story --srt
python main.py --input public/truyen.txt --voice vi-male-story-epic
```

---

## 6. Tùy chỉnh tốc độ và cao độ

### Dùng `--speed` (dễ nhất)

```bash
--speed 1.0    # bình thường
--speed 1.25   # nhanh hơn 25%
--speed 1.5    # nhanh hơn 50%
--speed 2.0    # nhanh gấp đôi
--speed 0.75   # chậm hơn 25%
```

```bash
python main.py --input public/sample.txt --speed 1.5
python main.py --input public/sample.txt --voice vi-male-story --speed 0.8
```

### Dùng `--rate` (edge-tts, nâng cao)

```bash
--rate "+20%"   # nhanh hơn 20%
--rate "-15%"   # chậm hơn 15%
```

### Dùng `--pitch` để chỉnh cao độ giọng

```bash
--pitch "+20Hz"   # cao hơn (giọng trẻ hơn)
--pitch "-30Hz"   # thấp hơn (giọng trầm hơn)
```

Kết hợp để thử nghiệm giọng riêng:

```bash
python main.py --input public/sample.txt \
  --voice vi-male \
  --rate -15% \
  --pitch -40Hz
```

---

## 7. Tạo phụ đề SRT

> **Lưu ý:** Chỉ hoạt động với `--engine edge-tts`.

```bash
# Tạo cả .mp3 và .srt
python main.py --input public/sample.txt --srt

# Kết quả:
#   output/sample.mp3
#   output/sample.srt

# Custom đường dẫn output
python main.py --input public/truyen.txt \
  --output output/truyen.mp3 \
  --srt \
  --srt-output output/truyen.srt

# Điều chỉnh số từ mỗi dòng phụ đề
python main.py --input public/sample.txt --srt --words-per-cue 5
```

Định dạng SRT được tạo ra:

```
1
00:00:00,100 --> 00:00:01,450
Xin chào! Đây là bài kiểm tra

2
00:00:01,500 --> 00:00:06,075
chuyển đổi văn bản thành giọng nói.
```

---

## 8. Toàn bộ tùy chọn CLI

```
python main.py [OPTIONS]

Tùy chọn chính:
  --input,  -i  FILE     File .txt đầu vào (bắt buộc)
  --output, -o  FILE     File audio đầu ra (mặc định: output/<tên>.mp3)
  --engine      ENGINE   TTS engine: edge-tts | gtts | kokoro (mặc định: edge-tts)
  --lang        LANG     Mã ngôn ngữ ISO 639-1: vi, en, fr, ja... (mặc định: vi)

Tốc độ:
  --speed       FLOAT    Hệ số tốc độ 0.5–2.0 (mặc định: 1.0)
  --rate        RATE     Rate offset edge-tts: "+10%" hoặc "-5%"

Tùy chọn edge-tts:
  --voice       VOICE    Preset hoặc tên voice đầy đủ (mặc định: vi-female)
  --pitch       PITCH    Cao độ: "-20Hz" hoặc "+15Hz"
  --volume      VOL      Âm lượng: "+10%" (mặc định: +0%)

Phụ đề:
  --srt                  Tạo file .srt (chỉ edge-tts)
  --srt-output  FILE     Đường dẫn custom cho .srt
  --words-per-cue N      Số từ mỗi dòng phụ đề (mặc định: 8)

Khác:
  --list-voices          Liệt kê tất cả preset và voice
  --verbose, -v          Bật log chi tiết
  --help,   -h           Hiển thị trợ giúp
```

---

## 9. So sánh các engine

| Tiêu chí | edge-tts | gTTS | Kokoro |
|---|:---:|:---:|:---:|
| **Tiếng Việt** | ✅ Rất tốt | ✅ Tốt | ❌ Không hỗ trợ |
| **Chất lượng giọng** | ⭐⭐⭐⭐⭐ Neural | ⭐⭐⭐⭐ Neural | ⭐⭐⭐⭐ Neural |
| **Cần internet** | ✅ Có | ✅ Có | ❌ Offline sau lần đầu |
| **Tạo SRT** | ✅ Có | ❌ Không | ❌ Không |
| **Điều chỉnh pitch** | ✅ Có | ❌ Không | ❌ Không |
| **Điều chỉnh tốc độ** | ✅ Chi tiết | ⚠️ Chỉ slow/fast | ✅ Tùy ý |
| **Cần cài thêm** | Không | `pip install gTTS` | `pip install kokoro soundfile` |
| **Định dạng output** | MP3 | MP3 | **WAV** |
| **API key** | Không | Không | Không |

**Khuyến nghị:**
- Tiếng Việt → **edge-tts** (chất lượng tốt nhất, có SRT)
- Cần dùng Google → **gTTS**
- Tiếng Anh offline → **Kokoro**

---

## 10. Cài đặt Kokoro (offline)

```bash
pip install kokoro soundfile
```

Lần đầu chạy, Kokoro tự động tải model ~82 MB từ HuggingFace:

```bash
python main.py --input public/story_en.txt --engine kokoro --lang en
```

### Voice Kokoro phổ biến

```
Nữ: af_bella, af_sarah, af_nicole, af_sky
Nam: am_adam, am_michael, bm_george (British)
```

```bash
python main.py --input public/story_en.txt \
  --engine kokoro \
  --lang en \
  --voice af_bella \
  --speed 0.9
```

### Ngôn ngữ Kokoro hỗ trợ

| `--lang` | Ngôn ngữ |
|---|---|
| `en` | American English |
| `en-gb` | British English |
| `es` | Tây Ban Nha |
| `fr` | Pháp |
| `hi` | Hindi |
| `it` | Ý |
| `ja` | Nhật |
| `ko` | Hàn |
| `pt` | Bồ Đào Nha |
| `zh` | Tiếng Trung |

---

## 11. Xử lý lỗi thường gặp

### `FileNotFoundError: Input file not found`

```bash
# Kiểm tra đường dẫn file
ls public/
python main.py --input public/ten_file.txt
```

### `gTTS is not installed`

```bash
pip install gTTS
```

### `kokoro is not installed`

```bash
pip install kokoro soundfile
```

### `ModuleNotFoundError: No module named 'edge_tts'`

```bash
pip install edge-tts
```

### Lỗi encoding file tiếng Việt

Tool tự thử nhiều encoding (UTF-8, UTF-16, Latin-1...). Nếu vẫn lỗi, hãy lưu file với encoding UTF-8:

```bash
# macOS / Linux
iconv -f latin1 -t utf-8 input.txt -o input_utf8.txt
```

### Chạy với log chi tiết để debug

```bash
python main.py --input public/sample.txt --verbose
```

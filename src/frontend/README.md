# Photo AI Tool — Frontend

App tĩnh (HTML/CSS/JS thuần, không cần build) được FastAPI phục vụ tại `/`.
Chọn chức năng → tải ảnh → xem kết quả + báo cáo QA. Không cần đăng nhập.

## Chạy

```powershell
# Từ gốc dự án
$env:PYTHONPATH = "src/backend;workers/src;."
python -m uvicorn photoai_api.main:app --host 127.0.0.1 --port 8000
# Mở http://127.0.0.1:8000
```

## Ghi chú thiết kế

- Không dùng framework/build step: hợp với self-host CPU, chạy ngay bằng `uvicorn`.
- Toàn bộ trạng thái (job, ảnh, QA report) nằm trong bộ nhớ của API — không database.
- Có thể thay bằng Next.js/React sau này; chỉ cần gọi đúng các endpoint:
  - `GET /api/recipes`
  - `POST /api/jobs` (multipart: `file`, `recipe_id`, `params`, `ownership_confirmed`)
  - `GET /api/jobs/{id}`, `GET /api/jobs/{id}/result`, `GET /api/jobs`

# HƯỚNG DẪN TRIỂN KHAI VÀ ĐÓNG GÓI (DEPLOYMENT GUIDE)

- **Hệ thống:** Phân hệ Tiếp nhận và phân loại bảo hành (L2) - Mekong Mobile
- **Sinh viên:** Nguyễn Bá Anh Khôi - 237480200247
- **Track:** Software Engineering (SE)

---

### 1. Triển khai cục bộ (Local Development)

#### Yêu cầu tiên quyết:
- Node.js version 20 LTS trở lên
- npm version 10 trở lên

#### Các bước khởi chạy:
```bash
# 1. Tạo biến môi trường từ mẫu
cp .env.example .env

# 2. Cài đặt phụ thuộc
npm install

# 3. Chạy kiểm thử tự động
npm test

# 4. Khởi chạy server API
npm run dev
# Mở trình duyệt kiểm tra: http://localhost:3000/health
```

---

### 2. Triển khai bằng Docker & Docker Compose (BT3)

#### Yêu cầu tiên quyết:
- Docker Desktop đã được cài đặt và đang chạy

#### Các bước thực hiện:
```bash
# 1. Khởi động toàn bộ cụm dịch vụ (PostgreSQL 16 + API Node.js)
docker compose up -d --build

# 2. Kiểm tra trạng thái container và healthcheck
docker compose ps

# 3. Kiểm tra log ứng dụng
docker compose logs -f api

# 4. Dừng cụm dịch vụ
docker compose down
```

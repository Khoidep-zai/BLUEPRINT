---
name: code-simplification
description: "Đơn giản hóa mã nguồn (/code-simplify), ưu tiên sự rõ ràng hơn là sự khéo léo thông minh (Clarity over Cleverness), loại bỏ tầng trừu tượng thừa và dọn dẹp nợ kỹ thuật."
---

# Code Simplification Skill (Đơn Giản Hóa Mã Nguồn & Tối Ưu Codespace)

Kỹ năng tinh gọn mã nguồn, loại bỏ các đoạn code rườm rà, lặp lại, và sắp xếp thư mục ngăn nắp, dễ đọc, dễ hiểu.

## 1. Nguyên Tắc "Clarity Over Cleverness"
- **Không tạo class/interface trừu tượng chỉ để bọc 1 hàm duy nhất:** Nếu một thao tác toán học là pure function, hãy để nó là hàm độc lập (như `subtle_perspective_chin_warp` hoặc `compose_luxury_studio_product`).
- **Đặt tên biến tường minh:** Dùng `original_rgb`, `skin_mask`, `high_freq` thay vì `img1`, `m`, `hf`.
- **Giảm độ sâu lồng nhau (Flatten Nested Logic):** Sử dụng guard clauses (Return early) để tránh các khối `if...else` lồng nhau sâu.

## 2. Tiêu Chuẩn Tổ Chức Codespace Ngăn Nắp
- Loại bỏ các file rác, file nháp, file trùng lặp hoặc thư mục tạm không thuộc dự án.
- Tách bạch rõ ràng giữa:
  - `storage/`: Đọc/ghi và định dạng dữ liệu (I/O).
  - `engine/`: Điều phối luồng và quản lý GPU.
  - `processors/`: Các thuật toán toán học và AI wrappers.
  - `detectors/`: Các bộ nhận diện khuôn mặt, vật thể, chữ.
  - `qa/`: Đo đạc số liệu chất lượng.
  - `ui/`: Tầng giao diện người dùng PySide6.

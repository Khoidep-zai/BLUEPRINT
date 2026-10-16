---
name: planning-and-task-breakdown
description: "Lập kế hoạch phân rã nhiệm vụ (/plan), chia nhỏ công việc thành các task nguyên tử (atomic), độc lập, có thể kiểm chứng từng bước bằng test."
---

# Planning & Task Breakdown Skill (Lập Kế Hoạch & Phân Rã Nhiệm Vụ)

Kỹ năng chia nhỏ các yêu cầu phức tạp (như thêm recipe AI mới, tối ưu hóa bộ nhớ, hoặc nâng cấp giao diện PySide6) thành chuỗi các nhiệm vụ vi mô có thể kiểm thử độc lập.

## 1. Nguyên Tắc Phân Rã Công Việc Nguyên Tử (Atomic Tasks)

- Mỗi task chỉ giải quyết **một trách nhiệm duy nhất**:
  - `Task 1`: Viết hàm toán học/CV thuần và test unit tương ứng.
  - `Task 2`: Viết wrapper model hoặc cập nhật storage codec.
  - `Task 3`: Cập nhật schema/recipe YAML và kiểm tra tính hợp lệ.
  - `Task 4`: Bổ sung widget / controls trên UI PySide6.
  - `Task 5`: Kiểm thử tích hợp toàn diện và kiểm tra giao diện không lỗi.
- **Không gom quá nhiều thay đổi trong một lần sửa:** Tránh sửa đồng thời cả thuật toán lõi, giao diện và cơ sở dữ liệu nếu chưa chốt từng phần.

## 2. Tiêu Chí Hoàn Thành (Definition of Done) Cho Mỗi Task
- Mã nguồn viết xong không có lỗi lint hoặc cú pháp.
- Unit test chạy xanh 100% (`pytest tests/ -q`).
- Không phá vỡ bất biến hệ thống (bảo toàn ảnh gốc, VRAM budget, strict PNG/JPG export).

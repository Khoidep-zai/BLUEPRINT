---
name: photo-recipe-engineering
description: "Cấu trúc dữ liệu 10 công thức chỉnh ảnh chuẩn nghiệp vụ (recipes/*.yaml), định dạng Schema Pydantic, bộ prompt song ngữ vi/en, và định tuyến bộ xử lý Hybrid CV + AI."
---

# Photo Recipe Engineering Skill (Kỹ Thuật Cấu Hình Công Thức Chỉnh Ảnh)

Kỹ năng định nghĩa, kiểm tra tính hợp lệ và tối ưu hóa 10 công thức nghiệp vụ chỉnh sửa ảnh trong Photo AI Desktop theo kiến trúc Data-Driven.

## 1. Bản Đồ 10 Chức Năng Nghiệp Vụ Chuẩn

1. `upscale_4k`: Siêu phân giải 4K giữ nguyên tỷ lệ, khử nhiễu JPEG, giữ màu sắc gốc bằng LAB histogram matching.
2. `skin_retouch`: Tách da BiSeNet, LaMa xóa mụn, Frequency Separation giữ 85% kết cấu lỗ chân lông thật.
3. `chin_fix`: Biến dạng hình học TPS nâng góc hàm 3% và giảm độ lộ cánh mũi, IC-Light làm dịu bóng cằm.
4. `open_eyes`: RetinaFace lọc người nhắm mắt ($EAR < 0.20$), Inpaint mở mắt tự nhiên và ghép Poisson Seamless.
5. `remove_watermark`: PaddleOCR + cọ vẽ người dùng, yêu cầu xác nhận bản quyền, LaMa tái tạo nền.
6. `remove_bystanders`: YOLOv8-seg + Depth-Anything tách người lạ và bóng đổ, giữ 100% pixel chủ thể chính.
7. `restore_old_photo`: Vá nếp rách ảnh cũ, CodeFormer khôi phục nét mặt, DDColor tô màu và thêm hạt phim 4K.
8. `golden_hour`: IC-Light chiếu nắng ấm giờ vàng, làm sáng sợi tóc ngược sáng (Rim-light), tiêm lại High-Freq gốc.
9. `low_light_fix`: Retinex cân bằng trắng khử ám vàng flash, nâng sáng vùng tối, làm dịu bóng gắt mũi/cằm.
10. `product_studio`: BiRefNet tách nền sản phẩm siêu nét, dựng bóng đổ tiếp xúc và phản chiếu mặt bàn sang trọng.

## 2. Cấu Trúc File Recipe YAML Chuẩn (`recipes/<id>.yaml`)

```yaml
id: skin_retouch
version: "1.0.0"
name_vi: "Làm Mịn Da Tự Nhiên & Giữ Lỗ Chân Lông"
name_en: "Natural Skin Retouch with Real Pores"
ownership_required: false

pipeline:
  detectors:
    - name: bisenet_face_parsing
      options:
        include_neck: true
        exclude: ["eyes", "eyebrows", "lips", "hair", "beard"]
  mask:
    type: skin_blemish_composite
    feather_radius: 5
  edit:
    editor: skin_frequency_retouch
    params:
      hf_restore_strength: 0.85
      low_freq_smooth_sigma: 3.0
      lama_acne_removal: true
  blend:
    mode: frequency_recombine
  qa:
    thresholds:
      identity_min: 0.95
      delta_e_max: 1.8
      texture_variance_min_ratio: 0.70

retry:
  max_attempts: 2
  strength_step: -0.1

prompt:
  vi: "prompts/skin_retouch.vi.md"
  en: "prompts/skin_retouch.en.md"
```

## 3. Quy Chuẩn Kiểm Tra Tính Hợp Lệ
Mọi recipe mới hoặc sửa đổi bắt buộc phải vượt qua bộ kiểm tra schema:
`pytest tests/unit/test_recipe_schema.py`
và kiểm thử tích hợp thực tế:
`pytest tests/integration/test_all_recipes.py`.

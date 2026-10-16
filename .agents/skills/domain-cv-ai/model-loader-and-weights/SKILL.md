---
name: model-loader-and-weights
description: "Cấu hình, đăng ký loader và nạp weights ngoại tuyến (.pth, .safetensors, .onnx) cho các model Real-ESRGAN, LaMa, CodeFormer, IC-Light, BiSeNet, BiRefNet, PaddleOCR."
---

# Model Loader & Weights Skill (Quản Lý Trọng Số Ngoại Tuyến)

Kỹ năng quản trị và đăng ký các bộ trọng số mạng nơ-ron (Model Weights) ngoại tuyến trong thư mục `models_weights/` cho Photo AI Desktop.

## 1. Danh Mục Các Model Cốt Lõi

| Model Key | Mục đích | Kiến trúc / Định dạng | Thư mục weights |
|---|---|---|---|
| `realesrgan` | Siêu phân giải 4K | Real-ESRGAN x4plus (`.pth`) | `models_weights/upscaler/` |
| `lama` | Xóa vật thể & mụn | LaMa Big-Large (`.pt` / `.onnx`) | `models_weights/inpaint/` |
| `codeformer` | Phục hồi nét mặt cổ | CodeFormer Fidelity (`.pth`) | `models_weights/face_restore/` |
| `ic_light` | Đổi ánh sáng & studio | IC-Light Relighting (`.safetensors`) | `models_weights/relight/` |
| `bisenet` | Tách 19 vùng mặt & da | BiSeNet Face Parsing (`.pth`) | `models_weights/parsing/` |
| `birefnet` | Tách nền sản phẩm/tóc | BiRefNet Dichotomous (`.pth`) | `models_weights/matting/` |
| `retinaface` | Phát hiện mặt & landmarks | InsightFace RetinaFace (`.onnx`) | `models_weights/detectors/` |

## 2. Cơ Chế Đăng Ký Loader Không Sửa Core (`register_model_loader`)

Hệ thống cho phép cắm weights thật thông qua interface `register_model_loader`:

```python
from photoai.engine.vram_manager import register_model_loader

def custom_lama_loader():
    import torch
    model = torch.jit.load("models_weights/inpaint/lama.pt")
    return model

register_model_loader("lama", custom_lama_loader)
```

## 3. Quy Tắc Bảo Mật Weights
- 100% weights đặt trong máy cục bộ, không tự động tải xuống qua HTTP khi app đang chạy.
- Ưu tiên định dạng an toàn `.safetensors` hoặc `.onnx` hơn `.pkl` để loại bỏ nguy cơ thực thi mã độc tùy ý.

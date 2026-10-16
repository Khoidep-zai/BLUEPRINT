---
name: gpu-vram-pipeline
description: "Quản lý tài nguyên VRAM GPU cục bộ (CUDA/MPS), VRAMModelManager singleton, PyTorch FP16/BF16, nạp và giải phóng model động, chống CUDA OOM trên GPU 8GB-12GB."
---

# GPU VRAM Pipeline Skill (Quản Lý Tài Nguyên VRAM & Pipeline GPU)

Kỹ năng quản lý vòng đời Deep Learning Models trên GPU cục bộ, tối ưu hóa bộ nhớ video (VRAM), ngăn chặn triệt để lỗi `CUDA Out of Memory` trên máy trạm cá nhân và laptop.

## 1. Nguyên Tắc Quản Lý VRAM (`src/photoai/engine/vram_manager.py`)

- **Singleton Pattern:** Duy nhất một đối tượng `VRAMModelManager` điều phối toàn bộ model.
- **Giới Hạn Ngặt Nghèo:** Tối đa 2 models được nạp đồng thời trên VRAM (`max_active_models = 2`).
- **Nạp Theo Nhu Cầu (On-demand Lazy Loading):** Chỉ nạp weights khi recipe bước vào stage cần model đó.
- **Tự Động Giải Phóng (LRU Eviction):**
  - Khi nạp model thứ 3, tự động chuyển model ít dùng nhất về CPU, gọi `del`, `gc.collect()` và `torch.cuda.empty_cache()`.
- **Độ Chính Xác Nửa (Half Precision FP16/BF16):**
  - Tiết kiệm 50% VRAM so với FP32 mà không làm suy giảm chất lượng thị giác.

```python
from photoai.engine.vram_manager import VRAMModelManager

manager = VRAMModelManager()
# Nạp model an toàn qua hàm loader
model = manager.get_model("lama", lambda: load_lama_weights())
```

## 2. Kỹ Thuật Xử Lý Ảnh Lớn Chống OOM (Tiled Processing)
- Đối với ảnh 4K (ví dụ $4096 \times 4096$), không đưa toàn bộ ảnh vào model upscale cùng lúc.
- Chia thành các ô gạch (Tiles) kích thước $512 \times 512$ hoặc $1024 \times 1024$, có vùng đệm phủ lấn (Overlap) $64\text{px}$.
- Ghép lại các tile bằng hàm trọng số Gaussian (Blend Feather) để triệt tiêu đường nối biên.

## 3. Quy Chuẩn Fallback Khi Không Có GPU
- Hệ thống tự động nhận diện thiết bị: `cuda` -> `mps` -> `cpu`.
- Khi máy chỉ có CPU hoặc thiếu model weights: Tự động chạy nhánh Classical CV tương đương (Lanczos, Telea Inpaint, Bilateral Filter) mà không gây dừng chương trình.

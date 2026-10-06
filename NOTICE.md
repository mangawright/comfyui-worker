# Third-party software and models in this image

This image bundles the following third-party software and model weights, unmodified.
Each is distributed under its own license; see the linked sources for the full terms.
Full license texts are in /licenses (CreativeML Open RAIL++-M, GPL-3.0, AGPL-3.0, Apache-2.0); MIT/BSD license texts ship with each package's source.

## Models

| File (under /comfyui/models) | Source | License |
|---|---|---|
| checkpoints/animagine-xl-4.0.safetensors | https://huggingface.co/cagliostrolab/animagine-xl-4.0 | CreativeML Open RAIL++-M (full text: /licenses/CreativeML-Open-RAIL++-M.md). The use-based restrictions in Attachment A apply to any use of this model. |
| checkpoints/arthemyComicsXL_v20.safetensors | Arthemy Comics XL v2.0 **by Arthemy** — https://civitai.com/models/462532/arthemy-comics-xl | CreativeML Open RAIL++-M with the Civitai addendum (permissions: sell generated images, use on generation services; the author must be credited). Full RAIL++-M text: /licenses/CreativeML-Open-RAIL++-M.md |
| controlnet/controlnet-union-sdxl-1.0-promax.safetensors (renamed from diffusion_pytorch_model_promax.safetensors) | https://huggingface.co/xinsir/controlnet-union-sdxl-1.0 | Apache License 2.0 |
| ipadapter/ip-adapter-plus-face_sdxl_vit-h.safetensors | https://huggingface.co/h94/IP-Adapter | Apache License 2.0 |
| clip_vision/CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors (renamed from models/image_encoder/model.safetensors) | https://huggingface.co/h94/IP-Adapter (OpenCLIP ViT-H-14, LAION-2B) | MIT License |
| upscale_models/RealESRGAN_x4plus_anime_6B.pth | https://github.com/xinntao/Real-ESRGAN | BSD 3-Clause License |
| ultralytics/bbox/face_yolov8n.pt, hand_yolov8n.pt | https://huggingface.co/Bingsu/adetailer | See the model card (trained with Ultralytics YOLOv8, AGPL-3.0) |

## Software

| Software | Source | License |
|---|---|---|
| ComfyUI | https://github.com/comfyanonymous/ComfyUI | GPL-3.0 |
| ComfyUI_IPAdapter_plus | https://github.com/cubiq/ComfyUI_IPAdapter_plus | GPL-3.0 |
| ComfyUI-Impact-Pack | https://github.com/ltdrdata/ComfyUI-Impact-Pack | GPL-3.0 |
| ComfyUI-Impact-Subpack | https://github.com/ltdrdata/ComfyUI-Impact-Subpack | AGPL-3.0 |
| Ultralytics | https://github.com/ultralytics/ultralytics | AGPL-3.0 |
| PyTorch | https://github.com/pytorch/pytorch | BSD-style |
| NVIDIA CUDA base image | https://hub.docker.com/r/nvidia/cuda | NVIDIA Deep Learning Container License |

The source code of the GPL/AGPL components is included in this image as installed
(Python sources under /comfyui and the Python environment under /venv) and is available
from the repositories above.

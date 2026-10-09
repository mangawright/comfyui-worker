# Third-party software and models in this image

This image bundles the following third-party software and model weights, unmodified.
Each is distributed under its own license; see the linked sources for the full terms.
Full license texts are in /licenses (CreativeML Open RAIL++-M, GPL-3.0, Apache-2.0); MIT/BSD license texts ship with each package's source.

## Models

| File (under /comfyui/models) | Source | License |
|---|---|---|
| checkpoints/animagine-xl-4.0.safetensors | https://huggingface.co/cagliostrolab/animagine-xl-4.0 | CreativeML Open RAIL++-M (full text: /licenses/CreativeML-Open-RAIL++-M.md). The use-based restrictions in Attachment A apply to any use of this model. |
| checkpoints/arthemyComicsXL_v20.safetensors | Arthemy Comics XL v2.0 **by Arthemy** — https://civitai.com/models/462532/arthemy-comics-xl | CreativeML Open RAIL++-M with the Civitai addendum (permissions: sell generated images, use on generation services; the author must be credited). Full RAIL++-M text: /licenses/CreativeML-Open-RAIL++-M.md |
| controlnet/controlnet-union-sdxl-1.0-promax.safetensors (renamed from diffusion_pytorch_model_promax.safetensors) | https://huggingface.co/xinsir/controlnet-union-sdxl-1.0 | Apache License 2.0 |
| ipadapter/ip-adapter-plus-face_sdxl_vit-h.safetensors | https://huggingface.co/h94/IP-Adapter | Apache License 2.0 |
| clip_vision/CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors (renamed from models/image_encoder/model.safetensors) | https://huggingface.co/h94/IP-Adapter (OpenCLIP ViT-H-14, LAION-2B) | MIT License |
| upscale_models/RealESRGAN_x4plus_anime_6B.pth | https://github.com/xinntao/Real-ESRGAN | BSD 3-Clause License |
| onnx_bbox/face_anime_v1.4_s.onnx (renamed from face_detect_v1.4_s/model.onnx) | https://huggingface.co/deepghs/anime_face_detection | MIT License |
| onnx_bbox/hand_anime_v1.0_s.onnx (renamed from hand_detect_v1.0_s/model.onnx) | https://huggingface.co/deepghs/anime_hand_detection | OpenRAIL (see the model card; its use-based restrictions apply to any use of this model) |
| loras/badanatomy_SDXL_negative_LORA_SeaArtXL_v1.safetensors | Bad Anatomy SD XL Negative LORA (Sea Art XL v1) — https://civitai.com/models/430961 | CreativeML Open RAIL-M with the Civitai permissions set by the author (sell generated images, use on generation services, no credit required) |
| loras/add-detail-xl.safetensors | Detail Tweaker XL **by w4r10ck** — https://civitai.com/models/122359 | CreativeML Open RAIL-M with the Civitai permissions set by the author (sell generated images, use on generation services; the author must be credited) |
| loras/DetailN_XL.safetensors (renamed from DetialN_XL.safetensors) | DetailN_XL — https://civitai.com/models/1317134 | CreativeML Open RAIL-M with the Civitai permissions set by the author (sell generated images, use on generation services, no credit required) |

### Models in the image built from Dockerfile.next

| File (under /comfyui/models) | Source | License |
|---|---|---|
| diffusion_models/z_image_turbo_bf16.safetensors, text_encoders/qwen_3_4b.safetensors, vae/ae.safetensors | Z-Image Turbo by Tongyi-MAI (Alibaba) — https://huggingface.co/Tongyi-MAI/Z-Image-Turbo (ComfyUI repackage: https://huggingface.co/Comfy-Org/z_image_turbo) | Apache License 2.0 |
| diffusion_models/flux-2-klein-4b.safetensors, vae/flux2-vae.safetensors | FLUX.2 [klein] 4B by Black Forest Labs — https://huggingface.co/black-forest-labs/FLUX.2-klein-4B (ComfyUI repackage: https://huggingface.co/Comfy-Org/vae-text-encorder-for-flux-klein-4b) | Apache License 2.0 |

### Models in the image built from Dockerfile.qwen

| File (under /comfyui/models) | Source | License |
|---|---|---|
| diffusion_models/qwen_image_2512_fp8_e4m3fn.safetensors, text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors, vae/qwen_image_vae.safetensors | Qwen-Image-2512 by Qwen (Alibaba) — https://huggingface.co/Qwen/Qwen-Image-2512 (ComfyUI repackage: https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI); text encoder Qwen2.5-VL-7B | Apache License 2.0 |
| loras/Qwen-Image-2512-Lightning-4steps-V1.0-bf16.safetensors, loras/Qwen-Image-2512-Lightning-8steps-V1.0-bf16.safetensors | Qwen-Image-2512-Lightning by LightX2V / ModelTC — https://huggingface.co/lightx2v/Qwen-Image-2512-Lightning | Apache License 2.0 |

## Software

| Software | Source | License |
|---|---|---|
| ComfyUI | https://github.com/comfyanonymous/ComfyUI | GPL-3.0 |
| ComfyUI_IPAdapter_plus | https://github.com/cubiq/ComfyUI_IPAdapter_plus | GPL-3.0 |
| ComfyUI-Impact-Pack | https://github.com/ltdrdata/ComfyUI-Impact-Pack | GPL-3.0 |
| onnx_bbox_detector (custom_nodes/onnx_bbox_detector in this repository; uses helpers of ComfyUI-Impact-Pack) | this repository | GPL-3.0 |
| ONNX Runtime | https://github.com/microsoft/onnxruntime | MIT License |
| PyTorch and the pytorch/pytorch base image (includes the NVIDIA CUDA/cuDNN runtime libraries) | https://github.com/pytorch/pytorch, https://hub.docker.com/r/pytorch/pytorch | BSD-style; CUDA/cuDNN under the NVIDIA licenses shipped in the base image |

The source code of the GPL components is included in this image as installed
(Python sources under /comfyui and the system Python environment) and is available
from the repositories above.

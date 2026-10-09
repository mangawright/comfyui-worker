# RunPod serverless worker: ComfyUI (API only) + a small job handler.
# Built by RunPod from this repository (GitHub integration). The build step must finish within 30 minutes,
# so we start from an image that already has PyTorch + CUDA.
FROM pytorch/pytorch:2.11.0-cuda12.8-cudnn9-runtime

# PyTorch lives in the system Python of the base image; installing into it is fine inside this container
ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_BREAK_SYSTEM_PACKAGES=1
RUN apt-get update && apt-get install -y --no-install-recommends git wget libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ComfyUI
ARG COMFY_REF=v0.33.1
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /comfyui && cd /comfyui && git checkout ${COMFY_REF} \
    && pip install -r /comfyui/requirements.txt

# Custom nodes: IP-Adapter, Impact Pack (detailer), and a small ONNX bbox detector for the detailer
# (custom_nodes/onnx_bbox_detector: runs YOLO-style ONNX models with onnxruntime, no Ultralytics)
RUN cd /comfyui/custom_nodes \
    && git clone --depth 1 https://github.com/cubiq/ComfyUI_IPAdapter_plus.git \
    && git clone --depth 1 https://github.com/ltdrdata/ComfyUI-Impact-Pack.git \
    && pip install segment-anything scikit-image piexif transformers opencv-python-headless scipy dill matplotlib onnxruntime
COPY custom_nodes/onnx_bbox_detector /comfyui/custom_nodes/onnx_bbox_detector

# Models (public weights, unmodified; see /licenses/NOTICE.md). File names are fixed because requests select models by name.
RUN wget -q -O /comfyui/models/checkpoints/animagine-xl-4.0.safetensors \
      https://huggingface.co/cagliostrolab/animagine-xl-4.0/resolve/main/animagine-xl-4.0.safetensors
# Arthemy Comics XL v2.0 by Arthemy (Civitai model 462532, version 1019183). Credit to the author is required.
RUN wget -q -O /comfyui/models/checkpoints/arthemyComicsXL_v20.safetensors \
      https://civitai.com/api/download/models/1019183
RUN wget -q -O /comfyui/models/controlnet/controlnet-union-sdxl-1.0-promax.safetensors \
      https://huggingface.co/xinsir/controlnet-union-sdxl-1.0/resolve/main/diffusion_pytorch_model_promax.safetensors
RUN mkdir -p /comfyui/models/ipadapter /comfyui/models/onnx_bbox \
    && wget -q -O /comfyui/models/clip_vision/CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors \
      https://huggingface.co/h94/IP-Adapter/resolve/main/models/image_encoder/model.safetensors \
    && wget -q -O /comfyui/models/ipadapter/ip-adapter-plus-face_sdxl_vit-h.safetensors \
      https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/ip-adapter-plus-face_sdxl_vit-h.safetensors \
    && wget -q -O /comfyui/models/upscale_models/RealESRGAN_x4plus_anime_6B.pth \
      https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth \
    && wget -q -O /comfyui/models/onnx_bbox/face_anime_v1.4_s.onnx \
      https://huggingface.co/deepghs/anime_face_detection/resolve/main/face_detect_v1.4_s/model.onnx \
    && wget -q -O /comfyui/models/onnx_bbox/hand_anime_v1.0_s.onnx \
      https://huggingface.co/deepghs/anime_hand_detection/resolve/main/hand_detect_v1.0_s/model.onnx

# LoRAs for anatomy, hands and details (Civitai; permissions allow selling generated images and use on generation services).
# Each download is checked against the SHA256 published by Civitai.
RUN mkdir -p /comfyui/models/loras \
    && wget -q -O /comfyui/models/loras/badanatomy_SDXL_negative_LORA_SeaArtXL_v1.safetensors \
      https://civitai.com/api/download/models/480129 \
    && wget -q -O /comfyui/models/loras/add-detail-xl.safetensors \
      https://civitai.com/api/download/models/135867 \
    && wget -q -O /comfyui/models/loras/DetailN_XL.safetensors \
      https://civitai.com/api/download/models/1486887 \
    && cd /comfyui/models/loras && printf '%s  %s\n' \
      c82230d282d4432e4129ee1ba3cf8e00247b77ecd871ab8368567f7c7f35e80c badanatomy_SDXL_negative_LORA_SeaArtXL_v1.safetensors \
      0d9bd1b873a7863e128b4672e3e245838858f71469a3cec58123c16c06f83bd7 add-detail-xl.safetensors \
      5450c6973c3c020e594473f7d560d672833caa3448b5856b9f1913ac75c419dc DetailN_XL.safetensors \
      | sha256sum -c -

# Optional extra models from a RunPod network volume (/runpod-volume/models), if one is attached
COPY extra_model_paths.yaml /comfyui/extra_model_paths.yaml

# Third-party licenses (redistribution notices)
COPY NOTICE.md /licenses/NOTICE.md
COPY licenses/ /licenses/

RUN pip install runpod requests
COPY handler.py /handler.py
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]

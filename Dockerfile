# RunPod serverless worker: ComfyUI (API only) + a small job handler.
# Built by RunPod from this repository (GitHub integration). The build step must finish within 30 minutes,
# so we start from an image that already has PyTorch + CUDA.
FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime

ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends git wget libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ComfyUI
ARG COMFY_REF=v0.33.1
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /comfyui && cd /comfyui && git checkout ${COMFY_REF} \
    && pip install -r /comfyui/requirements.txt

# Custom nodes: IP-Adapter, Impact Pack (detailer) and its subpack (bbox detector)
RUN cd /comfyui/custom_nodes \
    && git clone --depth 1 https://github.com/cubiq/ComfyUI_IPAdapter_plus.git \
    && git clone --depth 1 https://github.com/ltdrdata/ComfyUI-Impact-Pack.git \
    && git clone --depth 1 https://github.com/ltdrdata/ComfyUI-Impact-Subpack.git \
    && pip install segment-anything scikit-image piexif transformers opencv-python-headless scipy dill matplotlib "ultralytics>=8.3.162"

# Models (public weights, unmodified; see /licenses/NOTICE.md). File names are fixed because requests select models by name.
RUN wget -q -O /comfyui/models/checkpoints/animagine-xl-4.0.safetensors \
      https://huggingface.co/cagliostrolab/animagine-xl-4.0/resolve/main/animagine-xl-4.0.safetensors
RUN wget -q -O /comfyui/models/controlnet/controlnet-union-sdxl-1.0-promax.safetensors \
      https://huggingface.co/xinsir/controlnet-union-sdxl-1.0/resolve/main/diffusion_pytorch_model_promax.safetensors
RUN mkdir -p /comfyui/models/ipadapter /comfyui/models/ultralytics/bbox \
    && wget -q -O /comfyui/models/clip_vision/CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors \
      https://huggingface.co/h94/IP-Adapter/resolve/main/models/image_encoder/model.safetensors \
    && wget -q -O /comfyui/models/ipadapter/ip-adapter-plus-face_sdxl_vit-h.safetensors \
      https://huggingface.co/h94/IP-Adapter/resolve/main/sdxl_models/ip-adapter-plus-face_sdxl_vit-h.safetensors \
    && wget -q -O /comfyui/models/upscale_models/RealESRGAN_x4plus_anime_6B.pth \
      https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth \
    && wget -q -O /comfyui/models/ultralytics/bbox/face_yolov8n.pt https://huggingface.co/Bingsu/adetailer/resolve/main/face_yolov8n.pt \
    && wget -q -O /comfyui/models/ultralytics/bbox/hand_yolov8n.pt https://huggingface.co/Bingsu/adetailer/resolve/main/hand_yolov8n.pt

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

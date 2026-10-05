#!/bin/bash
# 入れ物の起動：ComfyUI を API だけで動かし（画面は使わない）、handler を動かす。
# モデル（ベースモデル・構図の指定・参照画像・拡大・顔と手の検出）は入れ物に入っている。追加のモデルは RunPod のネットワークボリューム
# （サーバーレスでは /runpod-volume）の models/ に置く（extra_model_paths.yaml）。
set -e

cd /comfyui
python main.py --listen 127.0.0.1 --port 8188 --disable-auto-launch --dont-print-server &

python /handler.py

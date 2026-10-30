"""RunPod のサーバーレスの入れ物（worker）。同じ入れ物の中で動く ComfyUI に、届いた仕事を頼む（2026-10-04 に A1111 から切り替え）。

次の2種類の仕事を受け付ける：
    {"input": {"action": "object_info"}}
        → {"object_info": <ComfyUI の /object_info の答え>}（ワークフローの組み立てに使う。アプリが覚えておく）
    {"input": {"action": "prompt", "workflow": {...}, "images": [{"name": "x.png", "image": "<PNG の base64>"}], "output": "<ノードの ID>",
               "files": [{"path": "loras/<フォルダ>/<名前>.safetensors", "url": "<期限つきの URL>"}]}}
        → {"images": ["<PNG の base64>", ...]}
    files は描く前に models/ の下へ取ってくる追加のモデル（無くてもよい）。同じ入れ物の中では1回だけ取り、多くなったら古いものから消す。
1回ごとに別の GPU で動くことがあるので、画像を上げる・ワークフローを送る・結果を受け取るを、この1つの仕事の中で行う。
失敗したときは {"error": "<わけ>"} を返す。
"""

from __future__ import annotations

import base64
import os
import time
from pathlib import Path, PurePosixPath

import requests
import runpod

COMFY_URL = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")
READY_TIMEOUT_SEC = int(os.environ.get("COMFY_READY_TIMEOUT", "900"))
REQUEST_TIMEOUT_SEC = int(os.environ.get("COMFY_REQUEST_TIMEOUT", "1800"))
POLL_SEC = 0.5
# GPU のメモリが足りなくて失敗したときは、ComfyUI のモデルとメモリを空けてから、もう1回だけやり直す
OOM_WORDS = ("out of memory", "allocation on device")
# 取ってきた追加のモデルの置き場と、1つのフォルダに残しておく数
MODELS_DIR = Path(os.environ.get("COMFY_MODELS", "/comfyui/models"))
KEEP_FILES = int(os.environ.get("KEEP_FILES", "40"))

session = requests.Session()


def wait_until_ready() -> None:
    """ComfyUI が起動して API に答えるまで待つ。"""
    started = time.time()
    while time.time() - started < READY_TIMEOUT_SEC:
        try:
            if session.get(f"{COMFY_URL}/system_stats", timeout=5).ok:
                return
        except requests.RequestException:
            pass
        time.sleep(1)
    raise RuntimeError("ComfyUI が時間内に起動しませんでした")


def run_prompt(inp: dict) -> dict:
    out = run_prompt_once(inp)
    if any(w in str(out.get("error", "")).lower() for w in OOM_WORDS):
        try:
            session.post(f"{COMFY_URL}/free", json={"unload_models": True, "free_memory": True}, timeout=60)
            time.sleep(3)
        except requests.RequestException:
            pass
        out = run_prompt_once(inp)
    return out


def fetch_files(files: list) -> str | None:
    """追加のモデルを models/ の下へ取ってくる。失敗したらわけを返す。"""
    for f in files:
        rel = PurePosixPath(str(f.get("path") or ""))
        if rel.parts[:1] != ("loras",) or ".." in rel.parts or rel.suffix != ".safetensors" or len(rel.parts) < 3:
            # loras/<フォルダ>/<名前> だけ（入れ物に入っているモデルの所には置かない・消さない）
            return f"取ってこられないファイルの置き場です: {rel}"
        dest = MODELS_DIR / Path(*rel.parts)
        if dest.exists():
            os.utime(dest)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(".part")
        try:
            with session.get(str(f["url"]), stream=True, timeout=(30, 600)) as r:
                r.raise_for_status()
                with tmp.open("wb") as out:
                    for chunk in r.iter_content(1 << 20):
                        out.write(chunk)
            tmp.replace(dest)
        except (requests.RequestException, OSError) as e:
            tmp.unlink(missing_ok=True)
            return f"ファイルを取ってこられませんでした（{rel}）: {e}"
        # 多くなったら、使っていない古いものから消す（入れ物のディスクを使い切らないように）
        kept = sorted(dest.parent.glob("*.safetensors"), key=lambda p: p.stat().st_mtime, reverse=True)
        for old in kept[KEEP_FILES:]:
            old.unlink(missing_ok=True)
    return None


def run_prompt_once(inp: dict) -> dict:
    err = fetch_files(inp.get("files") or [])
    if err:
        return {"error": err}
    for img in inp.get("images") or []:
        data = base64.b64decode(str(img["image"]).split(",", 1)[-1])
        r = session.post(
            f"{COMFY_URL}/upload/image",
            files={"image": (img["name"], data, "image/png")},
            data={"type": "input", "overwrite": "true"},
            timeout=60,
        )
        if not r.ok:
            return {"error": f"画像を上げられませんでした（{r.status_code}）: {r.text[:300]}"}
    r = session.post(f"{COMFY_URL}/prompt", json={"prompt": inp["workflow"]}, timeout=60)
    body = r.json() if r.content else {}
    if not r.ok or body.get("node_errors"):
        return {"error": f"ワークフローを受け付けませんでした（{r.status_code}）: {str(body)[:500]}"}
    pid = body["prompt_id"]
    started = time.time()
    while True:
        if time.time() - started > REQUEST_TIMEOUT_SEC:
            return {"error": "生成が時間内に終わりませんでした"}
        entry = (session.get(f"{COMFY_URL}/history/{pid}", timeout=30).json() or {}).get(pid)
        if entry:
            status = entry.get("status") or {}
            if status.get("status_str") == "error":
                msgs = [m for m in status.get("messages", []) if m and m[0] == "execution_error"]
                return {"error": msgs[0][1].get("exception_message", "生成でエラーが起きました") if msgs else "生成でエラーが起きました"}
            if status.get("completed") or entry.get("outputs"):
                break
        time.sleep(POLL_SEC)
    images = []
    for img in (entry.get("outputs", {}).get(str(inp.get("output"))) or {}).get("images") or []:
        v = session.get(
            f"{COMFY_URL}/view",
            params={"filename": img["filename"], "subfolder": img.get("subfolder", ""), "type": img.get("type", "temp")},
            timeout=60,
        )
        images.append(base64.b64encode(v.content).decode("ascii"))
    if not images:
        return {"error": "画像ができませんでした"}
    return {"images": images}


def handler(event: dict) -> dict:
    inp = event.get("input") or {}
    action = inp.get("action")
    if action == "object_info":
        return {"object_info": session.get(f"{COMFY_URL}/object_info", timeout=120).json()}
    if action == "prompt":
        return run_prompt(inp)
    return {"error": f"知らない仕事です: {action}"}


if __name__ == "__main__":
    wait_until_ready()
    runpod.serverless.start({"handler": handler})

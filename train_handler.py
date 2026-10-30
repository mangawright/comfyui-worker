"""RunPod のサーバーレスの、追加学習（LoRA）を作る入れ物（worker）。学習は公開の学習の道具（ai-toolkit）で行う。

次の仕事を受け付ける：
    {"input": {"action": "train",
               "images": [{"name": "001.png", "url": "<期限つきの URL>", "caption": "<説明文>"}],
               "base_url": "<ベースモデルのファイルの URL（無ければ config の name_or_path を使う）>",
               "config": {<ai-toolkit の process の1つ分。datasets・training_folder はここで埋める>},
               "upload_url": "<できた LoRA を PUT する期限つきの URL>"}}
        → {"size": <バイト数>, "sha256": "<16進>", "seconds": <学習の秒数>}
失敗したときは {"error": "<わけ>"} を返す。進み具合は「<今のステップ>/<全部>」で知らせる。
ネットワークボリューム（/runpod-volume）をつないでいれば、ベースモデルを取ってきたものをそこに残して使い回す。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import requests
import runpod

TOOLKIT = Path(os.environ.get("AI_TOOLKIT", "/ai-toolkit"))
VOLUME = Path("/runpod-volume")
CACHE = VOLUME / "cache" if VOLUME.is_dir() else Path("/tmp/cache")
STEP_RE = re.compile(r"(\d+)/(\d+)\s*\[")

session = requests.Session()


def download(url: str, dest: Path) -> None:
    tmp = dest.with_suffix(dest.suffix + ".part")
    with session.get(url, stream=True, timeout=(30, 1800)) as r:
        r.raise_for_status()
        with tmp.open("wb") as out:
            for chunk in r.iter_content(1 << 20):
                out.write(chunk)
    tmp.replace(dest)


def base_model(url: str) -> Path:
    """ベースモデルのファイル（取ってきたものは残して使い回す）"""
    CACHE.mkdir(parents=True, exist_ok=True)
    dest = CACHE / (hashlib.sha1(url.encode()).hexdigest()[:16] + ".safetensors")
    if not dest.exists():
        download(url, dest)
    return dest


def train(event: dict, inp: dict) -> dict:
    started = time.time()
    work = Path(tempfile.mkdtemp(prefix="lora_"))
    try:
        data = work / "data"
        data.mkdir()
        for img in inp.get("images") or []:
            name = Path(str(img["name"])).name
            download(str(img["url"]), data / name)
            (data / Path(name).with_suffix(".txt")).write_text(str(img.get("caption") or ""), encoding="utf-8")
        process = dict(inp["config"])
        process["training_folder"] = str(work / "out")
        process["datasets"] = [{**d, "folder_path": str(data)} for d in process.get("datasets") or [{}]]
        if inp.get("base_url"):
            process["model"] = {**process.get("model", {}), "name_or_path": str(base_model(str(inp["base_url"])))}
        config = {"job": "extension", "config": {"name": "lora", "process": [process]}, "meta": {"name": "lora", "version": "1.0"}}
        cfg = work / "config.json"
        cfg.write_text(json.dumps(config), encoding="utf-8")
        env = {**os.environ, "HF_HOME": str(CACHE / "hf")}
        proc = subprocess.Popen(
            ["python", "run.py", str(cfg)], cwd=TOOLKIT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
        )
        tail: list[str] = []
        last = ""
        assert proc.stdout is not None
        for line in proc.stdout:
            tail = (tail + [line.rstrip()])[-40:]
            m = STEP_RE.search(line)
            if m and m.group(0) != last:
                last = m.group(0)
                runpod.serverless.progress_update(event, f"{m.group(1)}/{m.group(2)}")
        if proc.wait() != 0:
            return {"error": "学習が失敗しました: " + "\n".join(tail)[-1500:]}
        outs = sorted((work / "out").rglob("*.safetensors"), key=lambda p: p.stat().st_mtime)
        if not outs:
            return {"error": "学習が終わりましたが、ファイルができていません"}
        result = outs[-1]
        digest = hashlib.sha256()
        with result.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                digest.update(chunk)
        size = result.stat().st_size
        with result.open("rb") as f:
            r = session.put(str(inp["upload_url"]), data=f, headers={"content-length": str(size)}, timeout=(30, 1800))
        if not r.ok:
            return {"error": f"できたファイルを送れませんでした（{r.status_code}）: {r.text[:300]}"}
        return {"size": size, "sha256": digest.hexdigest(), "seconds": round(time.time() - started, 1)}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def handler(event: dict) -> dict:
    inp = event.get("input") or {}
    if inp.get("action") == "train":
        try:
            return train(event, inp)
        except Exception as e:  # noqa: BLE001 わけを返す
            return {"error": f"{type(e).__name__}: {e}"[:1500]}
    return {"error": f"知らない仕事です: {inp.get('action')}"}


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})

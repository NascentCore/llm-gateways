#!/usr/bin/env python3
"""
将本地目录（及若干额外文件）以 PutObject 上传到火山引擎 TOS。

对应文档 `docs/per-model-token-profile-nohup-20260509T063432Z.md` 中服务器路径时，请先在本地执行 scp，再对本脚本传入 **本地路径**。

PutObject 产品说明见：<https://www.volcengine.com/docs/6349/74860?lang=zh>
Python 普通上传说明见：<https://www.volcengine.com/docs/6349/92800?lang=zh>

依赖：仓库根目录执行 `uv sync --extra tos`（安装 `tos` SDK）。

环境变量（勿写入仓库）：
  TOS_ACCESS_KEY（或 VOLC_ACCESS_KEY）
  TOS_SECRET_KEY（或 VOLC_SECRET_KEY）
  TOS_ENDPOINT（如 tos-cn-beijing.volces.com）
  TOS_REGION（如 cn-beijing）

示例：
  uv sync --extra tos
  export TOS_ACCESS_KEY=... TOS_SECRET_KEY=... TOS_ENDPOINT=tos-cn-beijing.volces.com TOS_REGION=cn-beijing
  uv run --extra tos python scripts/tos_upload_local_tree.py \\
    --bucket your-bucket \\
    --key-prefix llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/ \\
    --local-root ./per_model_token_md_nohup_20260509T063432Z \\
    --extra-file ./per_model_token_md_nohup_20260509T063432Z_brief.out
"""

from __future__ import annotations

import argparse
import mimetypes
import os
import sys
from pathlib import Path


def _env(*names: str) -> str:
    for n in names:
        v = os.environ.get(n)
        if v:
            return v
    return ""


def _guess_content_type(path: Path) -> str | None:
    mt, _ = mimetypes.guess_type(str(path))
    if mt:
        return mt
    if path.suffix.lower() == ".jsonl":
        return "application/x-ndjson"
    return "application/octet-stream"


def main() -> int:
    try:
        import tos
        from tos.exceptions import TosError
    except ImportError:
        print("错误: 未安装 tos。请执行: uv sync --extra tos", file=sys.stderr)
        return 2

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bucket", required=True, help="TOS 桶名")
    p.add_argument(
        "--key-prefix",
        required=True,
        help="对象键前缀，建议以 / 结尾，如 llm_gateways/batches/stem/",
    )
    p.add_argument(
        "--local-root",
        type=Path,
        required=True,
        help="已从服务器 scp 到本地的批次根目录（对应文档 /tmp/... 整棵树）",
    )
    p.add_argument(
        "--extra-file",
        type=Path,
        action="append",
        default=[],
        metavar="PATH",
        help="额外上传的文件，可重复（如 *_brief.out）",
    )
    p.add_argument("--dry-run", action="store_true", help="只打印将要上传的 object key，不调用 API")
    args = p.parse_args()

    ak = _env("TOS_ACCESS_KEY", "VOLC_ACCESS_KEY")
    sk = _env("TOS_SECRET_KEY", "VOLC_SECRET_KEY")
    endpoint = _env("TOS_ENDPOINT")
    region = _env("TOS_REGION")
    if not args.dry_run:
        if not ak or not sk or not endpoint or not region:
            print(
                "错误: 请设置 TOS_ACCESS_KEY、TOS_SECRET_KEY、TOS_ENDPOINT、TOS_REGION",
                file=sys.stderr,
            )
            return 2

    root = args.local_root.resolve()
    if not root.is_dir():
        print(f"错误: --local-root 不是目录: {root}", file=sys.stderr)
        return 2

    prefix = args.key_prefix.strip().replace("\\", "/")
    if prefix and not prefix.endswith("/"):
        prefix += "/"

    files: list[tuple[Path, str]] = []
    for fp in sorted(root.rglob("*")):
        if fp.is_file():
            rel = fp.relative_to(root).as_posix()
            files.append((fp, prefix + rel))
    for ef in args.extra_file:
        efp = ef.resolve()
        if not efp.is_file():
            print(f"错误: --extra-file 不是文件: {efp}", file=sys.stderr)
            return 2
        files.append((efp, prefix + efp.name))

    if not files:
        print("错误: 没有可上传的文件", file=sys.stderr)
        return 2

    if args.dry_run:
        for _, key in files:
            print(key)
        return 0

    client = tos.TosClientV2(ak, sk, endpoint, region)
    ok = 0
    for local_path, object_key in files:
        ctype = _guess_content_type(local_path)
        size = local_path.stat().st_size
        try:
            with local_path.open("rb") as fh:
                client.put_object(
                    args.bucket,
                    object_key,
                    content=fh,
                    content_length=size,
                    content_type=ctype,
                )
        except TosError as e:
            print(f"上传失败 {object_key}: {e}", file=sys.stderr)
            return 1
        ok += 1
        print(f"ok {ok}/{len(files)} {object_key}", flush=True)

    print(f"完成: {ok} 个对象 -> s3://{args.bucket}/{prefix}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

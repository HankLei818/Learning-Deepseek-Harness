"""浏览上游 fs-read 录制，行号与原 JSONL 一致。"""

import argparse
import json
from collections import Counter
from pathlib import Path


def describe(kind, data):
    if kind in ("turn/start", "turn/end"):
        return f"回合 {data['turn']}"
    if kind in ("step/start", "step/end"):
        return f"步骤 {data['step']}"
    if kind == "user/message":
        return data["source"]["kind"]
    if kind == "request/header":
        return data["reason"]
    if kind == "assistant/message":
        blocks = data["message"]["content"]
        visible = [b["name"] for b in blocks if b["type"] == "tool-call"]
        visible.extend(b["text"] for b in blocks if b["type"] == "text")
        return " · ".join(visible)
    if kind == "tool/call":
        return f"{data['name']} {data['arguments']}"
    if kind == "tool/result":
        # 只显示 read 工具返回的带行号的文件正文。
        text = data["message"]["content"][0]["text"]
        return " ".join(line for line in text.splitlines() if line.partition(":")[0].isdigit())
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before-result", action="store_true", help="在第一个工具结果前停下")
    parser.add_argument(
        "--source", type=Path, default=Path(__file__).with_name("fs-read.jsonl"),
        help="本课的 JSONL 摘录或上游 fs-read 原始快照",
    )
    options = parser.parse_args()
    seen = Counter()
    print("上游行号  事件                记录")
    with options.source.open(encoding="utf-8") as source:
        for line, record in enumerate(source, start=1):
            event = json.loads(record)
            kind = event["type"]
            if options.before_result and kind == "tool/result":
                break
            detail = describe(kind, event.get("data", {}))
            if detail is not None:
                print(f"{line:>8}  {kind:<18}  {detail}")
                seen[kind] += 1
    print(
        f"\n{seen['turn/start']} 个回合 · {seen['step/start']} 个步骤 · "
        f"{seen['tool/call']} 次工具调用 · {seen['tool/result']} 个工具结果"
    )


if __name__ == "__main__":
    main()

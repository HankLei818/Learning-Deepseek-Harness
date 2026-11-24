"""回放 Web 录制中最后一条回复的公开文本片段。"""

import json
from pathlib import Path


def main():
    path = Path(__file__).with_name("web-reply.json")
    event = json.loads(path.read_text(encoding="utf-8"))
    data = event["data"]
    text = ""
    for group in data["stream"]:
        if group["type"] != "text-chunks":
            continue
        for piece in group["texts"]:
            text += piece
            print(f"收到 {piece!r}，拼出的正文是 {text!r}")

    saved = data["message"]["content"][0]["text"]
    print(f"会话记录 {event['type']} 中的正文是 {saved!r}")
    if text != saved:
        raise SystemExit("片段拼出的正文与保存的回复不一致")


if __name__ == "__main__":
    main()

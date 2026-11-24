"""对照 fs-read 录制中两次请求之前已加入对话的消息。"""

import json
from pathlib import Path


def main():
    history = []
    path = Path(__file__).with_name("fs-read.jsonl")
    with path.open(encoding="utf-8") as records:
        for line, record in enumerate(records, start=1):
            event = json.loads(record)
            kind = event["type"]
            if kind == "assistant/message":
                # 此时看到的是本次回答出现之前的历史。
                step = event["data"]["step"]
                print(f"第 {step} 次请求（{len(history)} 条消息）")
                for entry in history:
                    print(f"  {entry}")

            if event.get("surfaceOp") == "append":
                entry = f"{line:>2}  {kind}"
                if kind == "user/message":
                    entry += f"  {event['data']['source']['kind']}"
                history.append(entry)


if __name__ == "__main__":
    main()

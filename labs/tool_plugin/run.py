"""用第十一课的本地模型端点，验证一个工具从注册到回传的全过程。"""

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from deepseek_harness import DeepSeekHarness

from ..local_model import local_model


def run(text):
    tool_name = "count_codepoints"

    def respond(request):
        result = next(
            (block for block in request["messages"][-1]["content"]
             if block["type"] == "tool_result"),
            None,
        )
        if result is not None:
            if result.get("is_error"):
                raise RuntimeError(f"工具返回错误：{result['content']}")
            return "".join(block["text"] for block in result["content"] if block["type"] == "text")
        if not any(tool["name"] == tool_name for tool in request["tools"]):
            raise RuntimeError("请求中没有 count_codepoints，请检查插件是否加载")
        return {"type": "tool_use", "id": "lesson_call", "name": tool_name, "input": {"text": text}}

    with TemporaryDirectory() as work, local_model(respond=respond) as url:
        root = Path(work)
        workspace = root / "workspace"
        workspace.mkdir()
        plugin = Path(__file__).resolve().with_name("count_codepoints.mjs")
        patch = root / "lesson.yml"
        patch_rows = [{"insert": [{"id": tool_name, "name": str(plugin)}]}]
        patch.write_text(json.dumps(patch_rows), encoding="utf-8")
        with DeepSeekHarness(
            profile="sdk-minimal",
            cwd=str(workspace),
            runtime_cwd=str(workspace),
            dsh_home=str(root / "home"),
            patches=(str(patch),),
            api_key="lesson-local",
            base_url=url,
        ) as harness:
            reply = harness.run(f"请用 {tool_name} 统计这段文本的 Unicode 码点数：{text}")

    call, = [event["data"] for event in reply.events
             if event["type"] == "tool/call" and event["data"]["name"] == tool_name]
    outcome, = [event["data"]["message"] for event in reply.events if event["type"] == "tool/result"
                and event["data"]["message"]["toolCallId"] == call["callId"]]
    actual_text = json.loads(call["arguments"])["text"]
    answer = outcome["content"][0]["text"]
    if outcome.get("isError") or reply.finish_reason != "completed":
        raise RuntimeError(f"工具任务失败：{reply.finish_reason}, {outcome}")
    if actual_text != text or answer != str(len(text)) or reply.final_response != answer:
        raise RuntimeError(f"输入、工具结果或最终答复与预期不符：{call}, {outcome}")
    print(f"tool/call   {call['name']}({actual_text!r})")
    print(f"tool/result {answer}")
    print(f"最终答复    {reply.final_response}")


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "学习🌱")

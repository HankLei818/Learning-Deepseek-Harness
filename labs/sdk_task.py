"""用真实的 Python SDK 跑一轮，模型端点固定回复 SDK_OK。"""

from pathlib import Path
from tempfile import TemporaryDirectory

from deepseek_harness import DeepSeekHarness
from local_model import local_model


def main():
    with TemporaryDirectory() as temp, local_model() as url:
        root = Path(temp)
        workspace = root / "workspace"
        workspace.mkdir()
        with DeepSeekHarness(
            profile="sdk-minimal",
            cwd=str(workspace),
            runtime_cwd=str(workspace),
            dsh_home=str(root / "home"),
            base_url=url,
            api_key="local-demo",
        ) as harness:
            result = harness.run("请回复 SDK_OK。", session_id="lesson-11")

        if result.finish_reason != "completed" or result.final_response != "SDK_OK":
            raise RuntimeError(f"任务未按预期完成：{result.finish_reason}, {result.final_response}")
        print(f"会话  {result.session_id}")
        print(f"答复  {result.final_response}")
        print(f"结束  {result.finish_reason}")


if __name__ == "__main__":
    main()

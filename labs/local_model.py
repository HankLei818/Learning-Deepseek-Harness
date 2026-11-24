"""第 11、12 课共用的本地模型端点，只监听本机。"""

import json
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread


def reply_events(answer, model):
    """把文字或一次工具调用编码成 Messages API 的流式响应。"""
    if isinstance(answer, str):
        block = {"type": "text", "text": ""}
        delta = {"type": "text_delta", "text": answer}
        reason = "end_turn"
    else:
        block = {"type": "tool_use", "id": answer["id"], "name": answer["name"], "input": {}}
        delta = {"type": "input_json_delta", "partial_json": json.dumps(answer["input"])}
        reason = "tool_use"

    yield {"type": "message_start", "message": {
        "type": "message", "role": "assistant", "id": "lesson-model", "model": model,
        "content": [], "usage": {"input_tokens": 1, "output_tokens": 0},
    }}
    yield {"type": "content_block_start", "index": 0, "content_block": block}
    yield {"type": "content_block_delta", "index": 0, "delta": delta}
    yield {"type": "content_block_stop", "index": 0}
    yield {"type": "message_delta", "delta": {"stop_reason": reason}, "usage": {"output_tokens": 1}}
    yield {"type": "message_stop"}


@contextmanager
def local_model(respond=None):
    """启动临时 HTTP 服务，回调可根据本轮请求返回文字或工具调用。"""
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path.split("?")[0] != "/v1/messages":
                self.send_error(404)
                return
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            answer = "SDK_OK" if respond is None else respond(request)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            for event in reply_events(answer, request["model"]):
                frame = f"event: {event['type']}\ndata: {json.dumps(event)}\n\n"
                self.wfile.write(frame.encode())

        def log_message(self, *args):
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            thread.join()

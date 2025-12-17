import json

import pytest

from app.vercel_ui_message_stream.schema import validateVercelUIMessageChunk


class TestVercelUIMessageSchema:
    def testValidate(self) -> None:
        """严格同步 vercel ai sdk zod 的校验规则"""

        corrects = [
            {"type": "start", "messageId": "msg_2171704531c045bca63d5612"},
            {"type": "text-start", "id": "123", "providerMetadata": None},
            {
                "type": "text-delta",
                "id": "text_b9f13677c90f4023ae4b4bf1",
                "delta": "\u76ee\u524d",
            },
        ]
        for m in corrects:
            assert validateVercelUIMessageChunk(m) is None

        invalids = [
            {
                "type": "tool-input-start",
                # 此属性多余，需要报错
                "id": "call_780e342bec8a419f9b6d15",
                "toolCallId": "call_780e342bec8a419f9b6d15",
                "toolName": "get_weather",
            }
        ]
        for m in invalids:
            with pytest.raises(Exception):
                print(json.dumps(m))
                validateVercelUIMessageChunk(m)

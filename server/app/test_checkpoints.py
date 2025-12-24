from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk, ToolMessage

checkpoints = [
    {
        "config": {
            "configurable": {
                "checkpoint_ns": "",
                "thread_id": "1",
                "user_id": "1",
                "checkpoint_id": "1f0dfe43-0117-62f4-bfff-6dbc59c4a2f9",
            }
        },
        "parent_config": None,
        "values": {"messages": []},
        "metadata": {"source": "input", "step": -1, "parents": {}},
        "next": ["__start__"],
        "tasks": [
            {
                "id": "2cdf67d0-40fe-6acc-1856-c404145dc340",
                "name": "__start__",
                "interrupts": (),
                "state": None,
            }
        ],
    },
    {
        "config": {
            "configurable": {
                "checkpoint_ns": "",
                "thread_id": "1",
                "user_id": "1",
                "checkpoint_id": "1f0dfe43-0127-6cbc-8000-96de76fd71de",
            }
        },
        "parent_config": {
            "configurable": {
                "checkpoint_ns": "",
                "thread_id": "1",
                "user_id": "1",
                "checkpoint_id": "1f0dfe43-0117-62f4-bfff-6dbc59c4a2f9",
            }
        },
        "values": {
            "messages": [
                HumanMessage(
                    content="武汉天气",
                    additional_kwargs={},
                    response_metadata={},
                    id="a537952a-2905-428a-b802-9d2e599b27ff",
                )
            ]
        },
        "metadata": {"source": "loop", "step": 0, "parents": {}},
        "next": ["model"],
        "tasks": [
            {
                "id": "e58ceb96-920d-f7cd-8cdb-38eac936cf3c",
                "name": "model",
                "interrupts": (),
                "state": None,
            }
        ],
    },
    {
        "config": {
            "configurable": {
                "checkpoint_ns": "",
                "thread_id": "1",
                "user_id": "1",
                "checkpoint_id": "1f0dfe43-1a00-6874-8001-86fab1ae72ce",
            }
        },
        "parent_config": {
            "configurable": {
                "checkpoint_ns": "",
                "thread_id": "1",
                "user_id": "1",
                "checkpoint_id": "1f0dfe43-0127-6cbc-8000-96de76fd71de",
            }
        },
        "values": {
            "messages": [
                HumanMessage(
                    content="武汉天气",
                    additional_kwargs={},
                    response_metadata={},
                    id="a537952a-2905-428a-b802-9d2e599b27ff",
                ),
                AIMessage(
                    content="",
                    additional_kwargs={
                        "tool_calls": [
                            {
                                "index": 0,
                                "id": "call_2c10731c60ce4f0fbd5010",
                                "type": "function",
                                "function": {
                                    "name": "get_weather",
                                    "arguments": '{"city": "武汉"}',
                                },
                            }
                        ]
                    },
                    response_metadata={
                        "finish_reason": "tool_calls",
                        "request_id": "3adc2233-a99e-43b0-85f4-529c257d873d",
                        "token_usage": {
                            "input_tokens": 168,
                            "output_tokens": 19,
                            "total_tokens": 187,
                            "prompt_tokens_details": {"cached_tokens": 0},
                        },
                    },
                    id="lc_run--019b4a99-ec01-71e1-b8f1-6b4b1e180168",
                    tool_calls=[
                        {
                            "name": "get_weather",
                            "args": {"city": "武汉"},
                            "id": "call_2c10731c60ce4f0fbd5010",
                            "type": "tool_call",
                        }
                    ],
                ),
            ]
        },
        "metadata": {"source": "loop", "step": 1, "parents": {}},
        "next": ["tools"],
        "tasks": [
            {
                "id": "6fd09081-d22d-a88f-350f-bd3886965486",
                "name": "tools",
                "interrupts": (),
                "state": None,
            }
        ],
    },
    {
        "config": {
            "configurable": {
                "checkpoint_ns": "",
                "thread_id": "1",
                "user_id": "1",
                "checkpoint_id": "1f0dfe43-1a37-6e8c-8002-401cf95d1493",
            }
        },
        "parent_config": {
            "configurable": {
                "checkpoint_ns": "",
                "thread_id": "1",
                "user_id": "1",
                "checkpoint_id": "1f0dfe43-1a00-6874-8001-86fab1ae72ce",
            }
        },
        "values": {
            "messages": [
                HumanMessage(
                    content="武汉天气",
                    additional_kwargs={},
                    response_metadata={},
                    id="a537952a-2905-428a-b802-9d2e599b27ff",
                ),
                AIMessage(
                    content="",
                    additional_kwargs={
                        "tool_calls": [
                            {
                                "index": 0,
                                "id": "call_2c10731c60ce4f0fbd5010",
                                "type": "function",
                                "function": {
                                    "name": "get_weather",
                                    "arguments": '{"city": "武汉"}',
                                },
                            }
                        ]
                    },
                    response_metadata={
                        "finish_reason": "tool_calls",
                        "request_id": "3adc2233-a99e-43b0-85f4-529c257d873d",
                        "token_usage": {
                            "input_tokens": 168,
                            "output_tokens": 19,
                            "total_tokens": 187,
                            "prompt_tokens_details": {"cached_tokens": 0},
                        },
                    },
                    id="lc_run--019b4a99-ec01-71e1-b8f1-6b4b1e180168",
                    tool_calls=[
                        {
                            "name": "get_weather",
                            "args": {"city": "武汉"},
                            "id": "call_2c10731c60ce4f0fbd5010",
                            "type": "tool_call",
                        }
                    ],
                ),
                ToolMessage(
                    content='{"武汉": "Sunny"}',
                    name="get_weather",
                    id="7970fe74-790f-4e7c-9590-3134176d9815",
                    tool_call_id="call_2c10731c60ce4f0fbd5010",
                ),
            ]
        },
        "metadata": {"source": "loop", "step": 2, "parents": {}},
        "next": ["model"],
        "tasks": [
            {
                "id": "6d8339da-a49f-327d-55b0-6caffe4df6b4",
                "name": "model",
                "interrupts": (),
                "state": None,
            }
        ],
    },
    {
        "config": {
            "configurable": {
                "checkpoint_ns": "",
                "thread_id": "1",
                "user_id": "1",
                "checkpoint_id": "1f0dfe43-1eb7-6746-8003-b562fc511440",
            }
        },
        "parent_config": {
            "configurable": {
                "checkpoint_ns": "",
                "thread_id": "1",
                "user_id": "1",
                "checkpoint_id": "1f0dfe43-1a37-6e8c-8002-401cf95d1493",
            }
        },
        "values": {
            "messages": [
                HumanMessage(
                    content="武汉天气",
                    additional_kwargs={},
                    response_metadata={},
                    id="a537952a-2905-428a-b802-9d2e599b27ff",
                ),
                AIMessage(
                    content="",
                    additional_kwargs={
                        "tool_calls": [
                            {
                                "index": 0,
                                "id": "call_2c10731c60ce4f0fbd5010",
                                "type": "function",
                                "function": {
                                    "name": "get_weather",
                                    "arguments": '{"city": "武汉"}',
                                },
                            }
                        ]
                    },
                    response_metadata={
                        "finish_reason": "tool_calls",
                        "request_id": "3adc2233-a99e-43b0-85f4-529c257d873d",
                        "token_usage": {
                            "input_tokens": 168,
                            "output_tokens": 19,
                            "total_tokens": 187,
                            "prompt_tokens_details": {"cached_tokens": 0},
                        },
                    },
                    id="lc_run--019b4a99-ec01-71e1-b8f1-6b4b1e180168",
                    tool_calls=[
                        {
                            "name": "get_weather",
                            "args": {"city": "武汉"},
                            "id": "call_2c10731c60ce4f0fbd5010",
                            "type": "tool_call",
                        }
                    ],
                ),
                ToolMessage(
                    content='{"武汉": "Sunny"}',
                    name="get_weather",
                    id="7970fe74-790f-4e7c-9590-3134176d9815",
                    tool_call_id="call_2c10731c60ce4f0fbd5010",
                ),
                AIMessage(
                    content="武汉的天气是晴天。",
                    additional_kwargs={},
                    response_metadata={
                        "finish_reason": "stop",
                        "request_id": "73839d5d-eae8-4956-ad41-f01051aed64c",
                        "token_usage": {
                            "input_tokens": 207,
                            "output_tokens": 7,
                            "total_tokens": 214,
                            "prompt_tokens_details": {"cached_tokens": 128},
                        },
                    },
                    id="lc_run--019b4a99-f655-7132-a97c-a9b6f64db14a",
                ),
            ]
        },
        "metadata": {"source": "loop", "step": 3, "parents": {}},
        "next": [],
        "tasks": [],
    },
]

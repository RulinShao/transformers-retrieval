#!/usr/bin/env python
# coding=utf-8

# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from .agent_types import AgentAudio, AgentImage, AgentText
from .agents import ReactAgent


def pull_message(step_log: dict, test_mode: bool = True):
    try:
        from gradio import ChatMessage
    except ImportError:
        if test_mode:

            class ChatMessage:
                def __init__(self, role, content, metadata=None):
                    self.role = role
                    self.content = content
                    self.metadata = metadata
        else:
            raise ImportError("Gradio should be installed in order to launch a gradio demo.")

    if step_log.get("rationale"):
        yield ChatMessage(role="assistant", content=step_log["rationale"])
    if step_log.get("tool_call"):
        used_code = step_log["tool_call"]["tool_name"] == "code interpreter"
        content = step_log["tool_call"]["tool_arguments"]
        if used_code:
            content = f"```py\n{content}\n```"
        yield ChatMessage(
            role="assistant",
            metadata={"title": f"🛠️ Used tool {step_log['tool_call']['tool_name']}"},
            content=str(content),
        )
    if step_log.get("observation"):
        yield ChatMessage(role="assistant", content=f"```\n{step_log['observation']}\n```")
    if step_log.get("error"):
        yield ChatMessage(
            role="assistant",
            content=str(step_log["error"]),
            metadata={"title": "💥 Error"},
        )


def stream_to_gradio(agent: ReactAgent, task: str, test_mode: bool = False, **kwargs):
    """Runs an agent with the given task and streams the messages from the agent as gradio ChatMessages."""

    try:
        from gradio import ChatMessage
    except ImportError:
        if test_mode:

            class ChatMessage:
                def __init__(self, role, content, metadata=None):
                    self.role = role
                    self.content = content
                    self.metadata = metadata
        else:
            raise ImportError("Gradio should be installed in order to launch a gradio demo.")

    for step_log in agent.run(task, stream=True, **kwargs):
        if isinstance(step_log, dict):
            for message in pull_message(step_log, test_mode=test_mode):
                yield message

    final_answer = step_log  # Last log is the run's final_answer

    if isinstance(final_answer, AgentText):
        yield ChatMessage(role="assistant", content=f"**Final answer:**\n```\n{final_answer.to_string()}\n```")
    elif isinstance(final_answer, AgentImage):
        yield ChatMessage(
            role="assistant",
            content={"path": final_answer.to_string(), "mime_type": "image/png"},
        )
    elif isinstance(final_answer, AgentAudio):
        yield ChatMessage(
            role="assistant",
            content={"path": final_answer.to_string(), "mime_type": "audio/wav"},
        )
    else:
        yield ChatMessage(role="assistant", content=str(final_answer))
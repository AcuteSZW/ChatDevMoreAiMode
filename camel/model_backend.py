# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =========== Copyright 2023 @ CAMEL-AI.org. All Rights Reserved. ===========
from abc import ABC, abstractmethod
from typing import Any, Dict

import openai
import tiktoken

from camel.typing import ModelType
from chatdev.statistics import prompt_cost
from chatdev.utils import log_visualize
from openai.types.chat import ChatCompletion

import os

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

class ModelBackend(ABC):
    r"""不同模型后端的基础类。可能是OpenAI API，本地LLM，单元测试的占位符等。"""

    @abstractmethod
    def run(self, *args, **kwargs):
        r"""运行查询到后端模型。如果 OpenAI API 的返回值不是预期的字典，则会引发 RuntimeError。返回值：Dict【str, Any】：所有后端都必须以 OpenAI 格式返回字典。"""
        pass


class OpenAIModel(ModelBackend):
    r"""OpenAI API在统一的ModelBackend接口中。"""

    def __init__(self, model_type: ModelType, model_config_dict: Dict) -> None:
        super().__init__()
        self.model_type = model_type
        self.model_config_dict = model_config_dict

    def run(self, *args, **kwargs):
        string = "\n".join([message["content"] for message in kwargs["messages"]])

        try:
            encoding = tiktoken.encoding_for_model(self.model_type.name)
            num_prompt_tokens = len(encoding.encode(string))
            gap_between_send_receive = 15 * len(kwargs["messages"])
            num_prompt_tokens += gap_between_send_receive
        except Exception as err:
            num_prompt_tokens = 0
        # Experimental, add base_url

        client = openai.OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=self.model_type.base_url,
        )

        num_max_token = self.model_type.num_tokens
        num_max_completion_tokens = num_max_token - num_prompt_tokens
        self.model_config_dict['max_tokens'] = num_max_completion_tokens

        # print("args:", args, "kwargs:", kwargs, "model:", self.model_type.name,
        #       "model_config_dict:", self.model_config_dict)
        response = client.chat.completions.create(*args, **kwargs, model=self.model_type.name,
                                                  **self.model_config_dict)

        cost = prompt_cost(
            self.model_type.name,
            num_prompt_tokens=response.usage.prompt_tokens,
            num_completion_tokens=response.usage.completion_tokens
        )

        log_visualize(
            "**[OpenAI_Usage_Info Receive]**\nprompt_tokens: {}\ncompletion_tokens: {}\ntotal_tokens: {}\ncost: ${:.6f}\n".format(
                response.usage.prompt_tokens, response.usage.completion_tokens,
                response.usage.total_tokens, cost))
        if not isinstance(response, ChatCompletion):
            raise RuntimeError("Unexpected return from OpenAI API")
        return response


class StubModel(ModelBackend):
    r"""A dummy model used for unit tests."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()

    def run(self, *args, **kwargs) -> Dict[str, Any]:
        ARBITRARY_STRING = "Lorem Ipsum"

        return dict(
            id="stub_model_id",
            usage=dict(),
            choices=[
                dict(finish_reason="stop",
                     message=dict(content=ARBITRARY_STRING, role="assistant"))
            ],
        )


class DataScopeAIModel(ModelBackend):
    def __init__(self, model_type: ModelType, model_config_dict: Dict) -> None:
        super().__init__()
        self.model_type = model_type
        self.model_config_dict = model_config_dict
        try:
            import dashscope
        except Exception as err:
            raise ValueError(
                "使用dashscope客户端调用模型API应先安装dashscope: pip install dashscope")
        self.client = dashscope.Generation()

    def run(self, *args, **kwargs):
        string = "\n".join([message["content"] for message in kwargs["messages"]])

        try:
            encoding = tiktoken.encoding_for_model(self.model_type.name)
            num_prompt_tokens = len(encoding.encode(string))
            gap_between_send_receive = 15 * len(kwargs["messages"])
            num_prompt_tokens += gap_between_send_receive
        except Exception as err:
            num_prompt_tokens = 0

        # Experimental, add base_url
        num_max_token = self.model_type.num_tokens
        num_max_completion_tokens = num_max_token - num_prompt_tokens
        self.model_config_dict['max_tokens'] = num_max_completion_tokens

        # print("args:", args, "kwargs:", kwargs, "model:", self.model_type.name,
        #       "model_config_dict:", self.model_config_dict)

        api_key = os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            api_key = OPENAI_API_KEY

        # DASHSCOPE_API_KEY
        response = self.client.call(model=self.model_type.name, api_key=api_key, **kwargs)
        """
        {
          "status_code": 200,
          "request_id": "fae19851-2184-98be-afc5-af21c83fc89a",
          "code": "",
          "message": "",
          "output": {
            "text": "当然可以，这里有一个简单又美味的三色蔬菜炖饭的菜谱，这道菜充分利用了萝卜、土豆和茄子的风味，既健康又营养。\n\n### 三色",
            "finish_reason": "stop"
          },
          "usage": {
            "input_tokens": 20,
            "output_tokens": 40,
            "total_tokens": 60
          }
        }"""
        cost = prompt_cost(
            self.model_type.name,
            num_prompt_tokens=response["usage"]["input_tokens"],
            num_completion_tokens=response["usage"]["output_tokens"],
        )

        log_visualize(
            "**[OpenAI_Usage_Info Receive]**\nprompt_tokens: {}\ncompletion_tokens: {}\n"
            "total_tokens: {}\ncost: ${:.6f}\n".format(
                response["usage"]["input_tokens"], response["usage"]["output_tokens"],
                response["usage"]["total_tokens"], cost))
        return response

class ModelFactory:
    r"""Factory of backend models.

    Raises:
        ValueError: in case the provided model type is unknown.
    """

    @staticmethod
    def create(model_type: ModelType, model_config_dict: Dict) -> ModelBackend:
        # print(f"Attempting to use model: {model_type.name}")
        if model_type.name == "stub":
            return StubModel(model_type, model_config_dict)
        if model_type.api_type == "openai":
            return OpenAIModel(model_type, model_config_dict)

        if model_type.platform == "qwen" and model_type.api_type == "self":
            model_class = DataScopeAIModel
        else:
            raise ValueError("模型 API 后端创建错误, model_name:{}, base_url: {}, api_type:{}".format(
                model_type.name, model_type.base_url, model_type.api_type))
        inst = model_class(model_type, model_config_dict)
        return inst

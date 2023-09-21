from langchain.chat_models import ChatOpenAI
from openai.api_resources.abstract.engine_api_resource import EngineAPIResource
from typing import Any, Mapping, Dict
from langchain.schema import ChatResult
from langchain.pydantic_v1 import root_validator
import os
import requests
from loguru import logger
import json


class CustomChatOpenAI(ChatOpenAI):

    model_version: str = ""

    @root_validator()
    def validate_environment(cls, values: Dict) -> Dict:
        values["client"] = CustomChatCompletion
        return values

    @property
    def _llm_type(self) -> str:
        return "custom-chat-model"

    def _create_chat_result(self, response: Mapping[str, Any]) -> ChatResult:
        for res in response["choices"]:
            if res.get("finish_reason", None) == "content_filter":
                raise ValueError(
                    "Azure has not provided the response due to a content filter "
                    "being triggered"
                )
        chat_result = super()._create_chat_result(response)

        if "model" in response:
            model = response["model"]
            if self.model_version:
                model = f"{model}-{self.model_version}"

            if chat_result.llm_output is not None and isinstance(
                    chat_result.llm_output, dict
            ):
                chat_result.llm_output["model_name"] = model

        return chat_result


class CustomChatCompletion(EngineAPIResource):
    chat_model_url = os.getenv("CHAT_MODEL_SERVICE_URL", "")

    @classmethod
    def create(cls, *args, **kwargs):
        payload = {
            'messages': kwargs.get("messages"),
            'functions': kwargs.get("functions", None),
        }
        response = requests.post(cls.chat_model_url, json=payload)
        logger.info("response = {}", response.text)
        return json.loads(response.text)

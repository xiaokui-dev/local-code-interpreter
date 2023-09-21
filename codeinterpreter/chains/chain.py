import json
from typing import List, Optional

from langchain.base_language import BaseLanguageModel
from langchain.schema import AIMessage, OutputParserException
from langchain.chat_models.openai import ChatOpenAI

from codeinterpreter.prompts import remove_dl_link_prompt, determine_modifications_prompt


def get_file_modifications(
        code: str,
        llm: BaseLanguageModel,
        retry: int = 2,
) -> Optional[List[str]]:
    if retry < 1:
        return None

    prompt = determine_modifications_prompt.format(code=code)

    result = llm.predict(prompt, stop="```")

    try:
        result = json.loads(result)
    except json.JSONDecodeError:
        result = ""
    if not result or not isinstance(result, dict) or "modifications" not in result:
        return get_file_modifications(code, llm, retry=retry - 1)
    return result["modifications"]


def remove_download_link(
        input_response: str,
        llm: BaseLanguageModel,
) -> str:
    messages = remove_dl_link_prompt.format_prompt(
        input_response=input_response
    ).to_messages()
    message = llm.predict_messages(messages)

    if not isinstance(message, AIMessage):
        raise OutputParserException("Expected an AIMessage")

    return message.content


def test_remove():
    llm = ChatOpenAI(model="gpt-3.5-turbo-0613")

    example = (
        "I have created the plot to your dataset.\n\n"
        "Link to the file [here](sandbox:/plot.png)."
    )
    print(remove_download_link(example, llm))


def test_get_file():
    llm = ChatOpenAI(model="gpt-3.5-turbo-0613")

    code = """
        import matplotlib.pyplot as plt

        x = list(range(1, 11))
        y = [29, 39, 23, 32, 4, 43, 43, 23, 43, 77]

        plt.plot(x, y, marker='o')
        plt.xlabel('Index')
        plt.ylabel('Value')
        plt.title('Data Plot')

        plt.show()
        """

    print(get_file_modifications(code, llm))

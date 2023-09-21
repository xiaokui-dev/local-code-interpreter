import base64
import logging
import re
from io import BytesIO
from uuid import uuid4
from loguru import logger
from langchain.agents import BaseSingleActionAgent, AgentExecutor
from langchain.tools import StructuredTool

from codeinterpreter.chains import remove_download_link, get_file_modifications
from codeinterpreter.agents import CustomFunctionsAgent
from codeinterpreter.prompts import system_message
from codeinterpreter.schema import CodeToolRequest, File, AIResponse, UserRequest
from codeinterpreter.custom_llm import CustomChatOpenAI

from codeinterpreter.localbox import (LocalBox, upload, download)


class CodeInterpreter:

    input_file: File = None
    output_files: list[File] = []

    def __init__(self):
        self.codebox = LocalBox()
        self.verbose = True
        self.llm = CustomChatOpenAI()
        self.agent_executor = self.agent_executor()

    def agent_executor(self) -> AgentExecutor:
        return AgentExecutor.from_agent_and_tools(
            agent=self.agent(),
            max_iterations=12,
            tools=self.tools(),
            verbose=self.verbose,
        )

    def tools(self) -> list[StructuredTool]:
        return [
            StructuredTool(
                name="python",
                description="Input a string of code to a ipython interpreter. "
                            "Write the entire code in a single string. This string can "
                            "be really long, so you can use the `;` character to split lines. "
                            "Variables are preserved between runs. ",
                func=self.run_handler,
                args_schema=CodeToolRequest,
            ),
        ]

    def agent(self) -> BaseSingleActionAgent:
        return CustomFunctionsAgent.from_llm_and_tools(
            llm=self.llm,
            tools=self.tools(),
            system_message=system_message
        )

    def run_handler(self, code: str) -> str:
        logger.info("code: = {}", code)
        output = self.codebox.run(code)
        if not isinstance(output.content, str):
            raise TypeError("Expected output.content to be a string.")

        if output.type == "image/png":
            filename = f"image-{uuid4()}.png"
            file_buffer = BytesIO(base64.b64decode(output.content))
            file_buffer.name = filename
            self.output_files.append(File(name=filename, content=file_buffer.read()))
            return f"Image {filename} got send to the user."

        elif output.type == "error":
            if "ModuleNotFoundError" in output.content:
                if package := re.search(
                        r"ModuleNotFoundError: No module named '(.*)'",
                        output.content,
                ):
                    self.codebox.install(package.group(1))
                    return (
                        f"{package.group(1)} was missing but"
                        "got installed now. Please try again."
                    )
            else:
                logging.error("error = {}", output.content)
                pass

        elif modifications := get_file_modifications(code, self.llm):
            for filename in modifications:
                if filename == self.input_file.name:
                    continue
                file_out = download(filename)
                if not file_out.content:
                    continue
                file_buffer = BytesIO(file_out.content)
                file_buffer.name = filename
                self.output_files.append(
                    File(name=filename, content=file_buffer.read())
                )
        return output.content

    def generate_response(self, user_msg: str, file: File = None, ):
        user_request = UserRequest(content=user_msg, file=file)
        try:
            self._input_handler(user_request)
            self.codebox.start()
            response = self.agent_executor.run(input=user_request.content)
            self.codebox.stop()
            return self._output_handler(response)
        except Exception as e:
            return AIResponse(
                content="Error in CodeInterpreter: "
                        f"{e.__class__.__name__}  - {e}"
            )

    def _input_handler(self, request: UserRequest) -> None:
        if not request.file:
            return
        if not request.content:
            request.content = (
                "I uploaded, just text me back and confirm that you got the file(s)."
            )
        request.content += "\n**The user uploaded the following files: **\n"
        request.content += f"[Attachment: {request.file.name}]\n"
        upload(request.file.name, request.file.content)
        self.input_file = request.file
        request.content += "**File(s) are now available in the cwd. **\n"

    def _output_handler(self, final_response: str):
        for file in self.output_files:
            if str(file.name) in final_response:
                final_response = re.sub(r"\n\n!\[.*\]\(.*\)", "", final_response)

        if self.output_files and re.search(r"\n\[.*\]\(.*\)", final_response):
            try:
                final_response = remove_download_link(final_response, self.llm)
            except Exception as e:
                if self.verbose:
                    print("Error while removing download links:", e)

        output_files = self.output_files
        self.output_files = []
        self.code_log = []

        return AIResponse(content=final_response, files=output_files)
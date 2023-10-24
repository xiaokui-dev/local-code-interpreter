import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from asyncio.subprocess import Process
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
from typing import List, Optional, Union
from uuid import uuid4
from abc import ABC
from uuid import UUID
import requests
from websockets.client import WebSocketClientProtocol
from websockets.exceptions import ConnectionClosedError
from websockets.sync.client import ClientConnection
from websockets.sync.client import connect as ws_connect_sync

from pydantic import BaseModel
from loguru import logger

jupyter_file_path = os.path.join(os.environ.get('HOME'), "Desktop/codeinterpreter/jupyter_file")


def _check_installed() -> None:
    try:
        distribution("jupyter-kernel-gateway")
    except PackageNotFoundError:
        print(
            "Make sure 'jupyter-kernel-gateway' is installed "
            "when using without a CODEBOX_API_KEY.\n"
            "You can install it with 'pip install jupyter-kernel-gateway'."
        )
        raise


class CodeBoxOutput(BaseModel):
    type: str
    content: str


class FileOutput(BaseModel):
    name: str
    content: Optional[bytes] = None


def upload(file_name: str, content: bytes):
    os.makedirs(jupyter_file_path, exist_ok=True)
    with open(os.path.join(jupyter_file_path, file_name), "wb") as f:
        f.write(content)

    return f"{file_name} uploaded successfully"


def download(file_name: str) -> FileOutput:
    with open(os.path.join(jupyter_file_path, file_name), "rb") as f:
        content = f.read()

    return FileOutput(name=file_name, content=content)


def list_files() -> List[FileOutput]:
    return [
        FileOutput(name=file_name, content=None)
        for file_name in os.listdir(jupyter_file_path)
    ]


class LocalBox(ABC):
    _jupyter_pids: List[int] = []

    def __init__(self, session_id: Optional[UUID] = None) -> None:
        self.session_id = session_id
        self.port: int = 8888
        self.kernel_id: Optional[dict] = None
        self.ws: Union[WebSocketClientProtocol, ClientConnection, None] = None
        self.jupyter: Union[Process, subprocess.Popen, None] = None

    def start(self):
        self.session_id = uuid4()
        os.makedirs(jupyter_file_path, exist_ok=True)
        self._check_port()
        logger.info("Starting kernel...")
        out = subprocess.PIPE
        _check_installed()
        try:
            python = Path(sys.executable).absolute()
            self.jupyter = subprocess.Popen(
                [
                    python,
                    "-m",
                    "jupyter",
                    "kernelgateway",
                    "--KernelGatewayApp.ip='0.0.0.0'",
                    f"--KernelGatewayApp.port={self.port}",
                ],
                stdout=out,
                stderr=out,
                cwd=jupyter_file_path,
            )
            self._jupyter_pids.append(self.jupyter.pid)
        except FileNotFoundError:
            raise ModuleNotFoundError(
                "Jupyter Kernel Gateway not found, please install it with:\n"
                "`pip install jupyter_kernel_gateway`\n"
                "to use the LocalBox."
            )
        while True:
            try:
                response = requests.get(self.kernel_url, timeout=270)
                if response.status_code == 200:
                    break
            except requests.exceptions.ConnectionError:
                pass
            logger.info("Waiting for kernel to start...")
            time.sleep(1)
        self._connect()
        return "started"

    def stop(self):
        try:
            if self.jupyter is not None:
                self.jupyter.terminate()
                self.jupyter.wait()
                self.jupyter = None
                time.sleep(2)
            else:
                for pid in self._jupyter_pids:
                    os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

        if self.ws is not None:
            try:
                if isinstance(self.ws, ClientConnection):
                    self.ws.close()
                else:
                    loop = asyncio.new_event_loop()
                    loop.run_until_complete(self.ws.close())
            except ConnectionClosedError:
                pass
            self.ws = None

        return "stopped"

    def _connect(self) -> None:
        response = requests.post(
            f"{self.kernel_url}/kernels",
            headers={"Content-Type": "application/json"},
            timeout=270,
        )
        self.kernel_id = response.json()["id"]
        if self.kernel_id is None:
            raise Exception("Could not start kernel")

        self.ws = ws_connect_sync(f"{self.ws_url}/kernels/{self.kernel_id}/channels")

    def _check_port(self) -> None:
        try:
            response = requests.get(f"http://localhost:{self.port}", timeout=270)
        except requests.exceptions.ConnectionError:
            pass
        else:
            if response.status_code == 200:
                self.port += 1
                self._check_port()

    def run(
            self,
            code: Optional[str] = None,
            file_path: Optional[os.PathLike] = None,
            retry=3,
    ) -> CodeBoxOutput:
        if not code and not file_path:
            raise ValueError("Code or file_path must be specified!")

        if code and file_path:
            raise ValueError("Can only specify code or the file to read_from!")

        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()

        # run code in jupyter kernel
        if retry <= 0:
            raise RuntimeError("Could not connect to kernel")
        if not self.ws:
            self._connect()
            if not self.ws:
                raise RuntimeError("Jupyter not running. Make sure to start it first.")

        # send code to kernel
        self.ws.send(
            json.dumps(
                {
                    "header": {
                        "msg_id": (msg_id := uuid4().hex),
                        "msg_type": "execute_request",
                    },
                    "parent_header": {},
                    "metadata": {},
                    "content": {
                        "code": code,
                        "silent": False,
                        "store_history": True,
                        "user_expressions": {},
                        "allow_stdin": False,
                        "stop_on_error": True,
                    },
                    "channel": "shell",
                    "buffers": [],
                }
            )
        )
        result = ""
        while True:
            try:
                if isinstance(self.ws, WebSocketClientProtocol):
                    raise RuntimeError("Mixing asyncio and sync code is not supported")
                received_msg = json.loads(self.ws.recv())
            except ConnectionClosedError:
                self.start()
                return self.run(code, file_path, retry - 1)

            if (
                    received_msg["header"]["msg_type"] == "stream"
                    and received_msg["parent_header"]["msg_id"] == msg_id
            ):
                msg = received_msg["content"]["text"].strip()
                if "Requirement already satisfied:" in msg:
                    continue
                result += msg + "\n"

            elif (
                    received_msg["header"]["msg_type"] == "execute_result"
                    and received_msg["parent_header"]["msg_id"] == msg_id
            ):
                result += received_msg["content"]["data"]["text/plain"].strip() + "\n"

            elif received_msg["header"]["msg_type"] == "display_data":
                if "image/png" in received_msg["content"]["data"]:
                    return CodeBoxOutput(
                        type="image/png",
                        content=received_msg["content"]["data"]["image/png"],
                    )
                if "text/plain" in received_msg["content"]["data"]:
                    return CodeBoxOutput(
                        type="text",
                        content=received_msg["content"]["data"]["text/plain"],
                    )
                return CodeBoxOutput(
                    type="error",
                    content="Could not parse output",
                )
            elif (
                    received_msg["header"]["msg_type"] == "status"
                    and received_msg["parent_header"]["msg_id"] == msg_id
                    and received_msg["content"]["execution_state"] == "idle"
            ):
                if len(result) > 500:
                    result = "[...]\n" + result[-500:]
                return CodeBoxOutput(
                    type="text", content=result or "code run successfully (no output)"
                )

            elif (
                    received_msg["header"]["msg_type"] == "error"
                    and received_msg["parent_header"]["msg_id"] == msg_id
            ):
                error = (
                    f"{received_msg['content']['ename']}: "
                    f"{received_msg['content']['evalue']}"
                )
                return CodeBoxOutput(type="error", content=error)

    def install(self, package_name: str):
        self.run(f"!pip install -q {package_name}")
        return f"{package_name} installed successfully"

    @property
    def kernel_url(self) -> str:
        return f"http://localhost:{self.port}/api"

    @property
    def ws_url(self) -> str:
        return f"ws://localhost:{self.port}/api"

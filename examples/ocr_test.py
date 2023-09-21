from codeinterpreter.code_interpreter import CodeInterpreter, File
from loguru import logger
import os


def main():
    ci = CodeInterpreter()
    user_request = "ocr an image for me and generate a text file."

    file = File.from_path(os.path.join(os.environ.get('HOME'), "Desktop/F0gzvXFagAEJ5AZ.jpeg"))

    response = ci.generate_response(user_request, file=file)

    logger.info("response.content = {} ", response.content)
    for file in response.files:
        logger.info("response.fileName = {}", file.name)


if __name__ == "__main__":
    main()

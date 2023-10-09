#FROM python:3.9-slim AS base
#
#RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
#    && sed -i 's/http:\/\/deb.debian.org/http:\/\/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
#    && apt-get update \
#    && apt-get install -y build-essential gdal-bin libgdal-dev tesseract-ocr
#

FROM xiaokuidocker/codeinterpreter:base-tag as build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    GDAL_CONFIG=/usr/bin/gdal-config

COPY ["./requirements.txt","/opt/"]

RUN python -m venv /opt/venv \
    && pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /opt/requirements.txt

FROM xiaokuidocker/codeinterpreter:build-tag AS runtime

WORKDIR /home
COPY ./codeinterpreter ./codeinterpreter

RUN chmod -R a-w /home/codeinterpreter

CMD ["streamlit", "run","codeinterpreter/app.py"]

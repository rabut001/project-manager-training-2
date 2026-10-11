FROM mcr.microsoft.com/devcontainers/javascript-node:24-bookworm

# tesseract は問題冊子の「問N」の位置を探すのに使う。
RUN apt-get update \
  && apt-get install -y --no-install-recommends python3-pip tesseract-ocr tesseract-ocr-jpn \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --break-system-packages --no-cache-dir -r /tmp/requirements.txt

FROM mcr.microsoft.com/devcontainers/javascript-node:24-bookworm

# tesseract は問題冊子の「問N」の位置を探すのに使う。
RUN apt-get update \
  && apt-get install -y --no-install-recommends python3-pip tesseract-ocr tesseract-ocr-jpn \
  && rm -rf /var/lib/apt/lists/*

# gh はリポジトリの作成、Pages の設定、Actions の確認に使う。
RUN mkdir -p -m 755 /etc/apt/keyrings \
  && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg -o /etc/apt/keyrings/githubcli-archive-keyring.gpg \
  && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
  && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list \
  && apt-get update \
  && apt-get install -y --no-install-recommends gh \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --break-system-packages --no-cache-dir -r /tmp/requirements.txt

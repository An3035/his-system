# ==============================================================
# HIS 系统 Dockerfile
# 构建: docker build -t his-system .
# ==============================================================
FROM python:3.10-slim

# ── 第一步：替换 Debian 源为阿里云镜像（加速 apt 下载）──────
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's|security.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources

# ── 第二步：安装系统依赖 ─────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── 第三步：安装 uv（通过清华 PyPI 镜像）──────────────────────
RUN pip install --no-cache-dir uv -i https://pypi.tuna.tsinghua.edu.cn/simple

# ── 第四步：设置工作目录 ─────────────────────────────────────
WORKDIR /app

# ── 第五步：先复制依赖文件（利用 Docker 层缓存）──────────────
COPY pyproject.toml uv.lock ./

# ── 第六步：安装 Python 依赖 ──────────────────────────────────
# 注意：不加 --frozen，避免 Windows 锁文件在 Linux 上因平台差异报错
RUN uv sync --no-dev --index-url https://pypi.tuna.tsinghua.edu.cn/simple

# ── 第七步：复制项目源码（不含 .env，见 .dockerignore）───────
COPY . .

# ── 第八步：暴露端口 ─────────────────────────────────────────
EXPOSE 8000

# ── 启动 ─────────────────────────────────────────────────────
# uv run 会自动使用 .venv 中的依赖
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

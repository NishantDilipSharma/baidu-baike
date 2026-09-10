FROM python:3.12-slim

WORKDIR /app

# Install system dependencies if required for lxml and curl-cffi compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN pip install --no-cache-dir .

ENV PYTHONIOENCODING=utf-8
ENV PYTHONUTF8=1

ENTRYPOINT ["python", "-m", "baidu_baike_mcp"]

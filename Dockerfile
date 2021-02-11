FROM python:3.7-slim

LABEL maintainer="nicolas.ramy@darkelda.com"

ENV PYTHONDONTWRITEBYTECODE 0

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
                    gcc \
                    git \
                    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /app /workspace
WORKDIR /app
COPY . /app

RUN python setup.py install

VOLUME ["/app", "/workspace"]

CMD ["bash"]

ARG BASE=nvidia/cuda:11.8.0-base-ubuntu22.04
FROM ${BASE}

# Install OS dependencies:
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y --no-install-recommends \
    gcc g++ \
    make \
    python3 python3-dev python3-pip python3-venv python3-wheel 
RUN pip3 install --upgrade transformers accelerate datasets[audio] openai-whisper pyannote.audio
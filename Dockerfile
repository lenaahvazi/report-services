# syntax=docker/dockerfile:1

FROM python:3.11.4-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MPLCONFIGDIR=/app/matplotlib

WORKDIR /app

ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Create writable directories
RUN mkdir -p /app/matplotlib && \
    chmod -R 777 /app/matplotlib && \
    chmod -R 777 /

# Delete the contents of /app directory
RUN rm -rf /app/*

COPY main.py /app
COPY config.py /app
COPY . /app

RUN chmod o+w /app/config.py && \
    chmod 666 /app/config.py

# Copy requirements.txt and install dependencies
COPY requirements.txt /app/
RUN python -m pip install --no-cache-dir -r requirements.txt

# Switch to non-privileged user
USER appuser

# Expose the port that the application listens on
EXPOSE 7020

# Run the application
CMD ["python3", "main.py"]

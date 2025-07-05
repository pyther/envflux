# -------- Stage 1: Build --------
FROM python:3.13-alpine as builder

# Install system build tools and dependencies
RUN apk add --no-cache --virtual .build-deps \
    build-base libffi-dev openssl-dev cargo

WORKDIR /app

# Copy only what we need to install dependencies
COPY pyproject.toml ./

# Install the package and dependencies into /install
RUN pip install --upgrade pip \
    && pip install --prefix=/install . \
    && rm -rf /root/.cache/pip

# -------- Stage 2: Runtime --------
FROM python:3.13-alpine

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create non-root user
# Create a home directory for appuser and set permissions
RUN adduser -D -h /home/appuser appuser \
    && mkdir -p /home/appuser/.cache/envflux

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Set working directory
WORKDIR /app

# Copy application source
COPY envflux/ envflux/

# Switch to non-root user
USER appuser

# Set entrypoint
ENTRYPOINT ["python", "-m", "envflux", "--config", "/config/config.yaml"]


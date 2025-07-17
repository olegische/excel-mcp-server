# Stage 1: Builder - Installs base dependencies and build tools
FROM python:3.12-slim-bookworm AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Create a virtual environment and install dependencies, including build tools
RUN uv venv && \
    . .venv/bin/activate && \
    uv pip sync pyproject.toml && \
    uv pip install build setuptools wheel

# Stage 2: Compiler - Compiles the Cython code and builds a wheel
FROM python:3.12-slim-bookworm AS compiler

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy all necessary source and metadata files
COPY src ./src
COPY setup.py ./
COPY pyproject.toml ./
COPY README.md ./

# Copy the virtual environment with all dependencies from the builder stage
COPY --from=builder /app/.venv ./.venv

# Activate venv, compile, and build the wheel using standard tools
RUN . .venv/bin/activate && \
    # Build the Cython extensions in-place
    python setup.py build_ext --inplace && \
    # Strip debug symbols for smaller size
    find ./src -name "*.so" -exec strip -s {} \; || true && \
    # Build the wheel using the 'build' package (PEP 517)
    python -m build --wheel --outdir /app/dist .

# Stage 3: Final - Creates the lean, production-ready image
FROM python:3.12-slim-bookworm

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set environment variables for the runtime.
# The application reads EXCEL_FILES_PATH to know where to create/read files.
# This makes the path configurable at runtime.
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    EXCEL_FILES_PATH=/app/excel_files

# Create user and the venv directory.
# The data directory itself is created by the docker-compose volume mount.
RUN groupadd -r app && useradd -r -g app app && \
    mkdir -p /app/.venv && \
    chown -R app:app /app/.venv

# Switch to the non-root user for all subsequent operations
USER app

# Create a new virtual environment without caching
RUN uv venv --no-cache

# Copy the built wheel from the compiler stage, setting ownership to the app user
COPY --from=compiler --chown=app:app /app/dist/*.whl /tmp/

# Install the wheel into the venv and then clean up the temporary file
RUN . .venv/bin/activate && \
    uv pip install --no-cache /tmp/*.whl && \
    rm /tmp/*.whl

# Declare the data directory as a volume. This is good practice and allows
# Docker to manage the mount point correctly.
VOLUME /app/excel_files

# Set the command to run the server using the installed entry point
CMD ["excel-mcp-server", "sse"]

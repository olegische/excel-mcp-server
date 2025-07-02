# Stage 1: Builder - Prepares the application and its dependencies
FROM python:3.12-slim-bookworm AS builder

# Install uv, a fast Python package installer from Astral
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Set environment variables for the build process
ENV UV_COMPILE_BYTECODE=1

# Copy dependency definition files
COPY pyproject.toml ./
COPY uv.lock ./
COPY README.md ./

# Copy the application source code
COPY src ./src/

# Create a virtual environment and install the project and its dependencies.
# Installing with `.` makes our `excel_mcp` package available in the venv.
RUN uv venv && \
  uv pip install -e .

# Stage 2: Final - Creates the lean, production-ready image
FROM python:3.12-slim-bookworm

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN groupadd -r app && useradd -r -g app app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY pyproject.toml /app/

# Set environment variables for the runtime
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONPATH="/app" \
    # Configure the path for Excel files within the container
    EXCEL_FILES_PATH=/app/excel_files

# Create the directory for Excel files, set permissions, and declare it as a volume
RUN mkdir -p $EXCEL_FILES_PATH && chown -R app:app $EXCEL_FILES_PATH
VOLUME $EXCEL_FILES_PATH

# Expose the port the SSE server will run on
EXPOSE 8660

# Switch to the non-root user before running the application
USER app

# Set the command to run the server in SSE mode.
# The original CMD was incorrect and has been fixed.
CMD ["python", "-m", "src.excel_mcp", "sse"]

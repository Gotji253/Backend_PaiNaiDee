# Stage 1: Builder
FROM python:3.9-slim AS builder

# Set working directory
WORKDIR /app

# Copy the dependencies file
COPY pai_nai_dee_backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Stage 2: Final image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Create a non-root user
RUN addgroup --system app && adduser --system --group app

# Switch to the non-root user
USER app

# Copy the installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/

# Copy the application code
COPY --chown=app:app pai_nai_dee_backend/ ./

# Expose the port the app runs on
EXPOSE 8000

# Add a healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD [ "python", "-c", "import httpx; httpx.get('http://localhost:8000/health')" ]

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

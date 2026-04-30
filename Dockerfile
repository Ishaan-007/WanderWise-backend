# Use a lightweight Python image
FROM python:3.10-slim

# Set environment variables to prevent Python from writing .pyc files and to enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies needed for some Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker layer caching
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Create a non-root user for better security and set ownership of the app directory
RUN useradd -m appuser \
    && chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose the application port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# Official lightweight Python base image
FROM python:3.11-slim

# Avoid buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# Set working directory inside container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Generate and initialize local database on build/container start
RUN python src/data_cleaning.py && python src/database.py

# Expose standard Streamlit port
EXPOSE 8501

# Streamlit healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Command to run Streamlit on Google Cloud Run or standard container host
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

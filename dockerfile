# Specify the base image and platform architecture as required
FROM --platform=linux/amd64 python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies, including CPU-only PyTorch
RUN pip install --no-cache-dir -r requirements.txt

# --- This is the CRUCIAL step for offline execution ---
# Download and cache the sentence-transformer model inside the image
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2', cache_folder='/app/model_cache')"

# --- DIAGNOSTIC STEP ---
# List the contents of the cache folder to see the exact path
RUN ls -R /app/model_cache

# Copy your source code and the new entrypoint script
COPY ./src /app/src
COPY entrypoint.sh .

# Make the entrypoint script executable
RUN chmod +x entrypoint.sh

# Set the entrypoint to our new script
ENTRYPOINT ["./entrypoint.sh"]
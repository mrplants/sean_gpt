# Use an official Python runtime as a parent image
FROM python:3.10

# Upgrade pip
RUN pip install --upgrade pip

# Set the working directory to /app
WORKDIR /app

# Install dependencies needed for downloading and parsing
RUN apt-get update && apt-get install -y curl jq

# Set environment variable for your GitHub repo
ENV GITHUB_REPO=mrplants/sean_gpt

# Install the latest release from GitHub
RUN LATEST_RELEASE_URL=$(curl -s "https://api.github.com/repos/$GITHUB_REPO/releases/latest" | jq -r '.assets[] | select(.name | endswith(".whl")) | .browser_download_url') && \
    FILENAME=$(basename $LATEST_RELEASE_URL) && \
    echo "Downloading from: $LATEST_RELEASE_URL" && \
    if [ -z "$LATEST_RELEASE_URL" ]; then echo "No wheel file found in latest release" && exit 1; fi && \
    curl -L $LATEST_RELEASE_URL -o $FILENAME && \
    if [ ! -f $FILENAME ]; then echo "Failed to download wheel file" && exit 1; fi && \
    pip install $FILENAME

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "sean_gpt.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Use the ubuntu base image
FROM python:3.10
ARG WHEEL_FILE

# Set the working directory to /app
WORKDIR /app

# Copy in the requirements.txt file
COPY dist/requirements.txt .

# Install the requirements
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the specific wheel file
COPY dist/"$WHEEL_FILE" .

# Install the wheel
RUN pip install "$WHEEL_FILE"

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "sean_gpt.main:app", "--host", "0.0.0.0", "--port", "8000"]

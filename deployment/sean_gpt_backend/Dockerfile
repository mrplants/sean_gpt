# Use an official Python runtime as a parent image
FROM python:3.10
RUN pip install --upgrade pip

# Set the working directory to /app
WORKDIR /app

# Copy the requirements for the package so we can install them before the package.
# This allows caching dependencies.
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# Install the package
COPY sean_gpt-0.1.0-py3-none-any.whl /app/sean_gpt-0.1.0-py3-none-any.whl

# Install the package
RUN pip install sean_gpt-0.1.0-py3-none-any.whl

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "sean_gpt.main:app", "--host", "0.0.0.0", "--port", "8000"]
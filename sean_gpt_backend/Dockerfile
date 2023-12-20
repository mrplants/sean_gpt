# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory to /app
WORKDIR /app

# Download the git repo
RUN wget https://raw.githubusercontent.com/mrplants/sean_gpt/main/dist/sean_gpt-0.1.0-py3-none-any.whl

# Install the package
RUN pip install sean_gpt-0.1.0-py3-none-any.whl

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "sean_gpt.main:app", "--host", "0.0.0.0", "--port", "8000"]
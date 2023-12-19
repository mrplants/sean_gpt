# Use an official Python runtime as a parent image
FROM python:3.10

RUN apt update
RUN apt install -y pipx
RUN pipx ensurepath

# Install Poetry
RUN pipx install poetry

# Install git
RUN apt-get update && apt-get install -y git

# Download the git repo
RUN git clone https://github.com/mrplants/sean_gpt.git

# Install the dependencies
RUN poetry install

# Move into the directory
WORKDIR /sean_gpt

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["Poetry", "run", "uvicorn", "sean_gpt.main:app", "--host", "0.0.0.0", "--port", "8000"]
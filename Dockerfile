# Use an official Python runtime as a parent image
FROM docker.io/python:3.9-alpine

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY README.md /app
COPY poetry.lock /app
COPY pyproject.toml /app

# Install any needed packages
RUN pip install --trusted-host pypi.python.org poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

COPY static /app/static
COPY templates /app/templates
COPY minicloak.py /app

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run minicloak.py when the container launches
ENTRYPOINT ["python", "minicloak.py"]

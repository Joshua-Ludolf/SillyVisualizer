# Use an official Python runtime as a parent image
FROM python:3.11-alpine3.21

# Update OS packages to address known vulnerabilities
RUN apk update && apk upgrade && \
	apk add --no-cache build-base musl-dev linux-headers graphviz ttf-dejavu && \
	rm -rf /var/cache/apk/*

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
	pip install --no-cache-dir gunicorn

# Make port 3000 available to the world outside this container
EXPOSE 3000

# Define environment variable
ENV PYTHONUNBUFFERED=1

# Run the application
# Gunicorn with threads (good default for Flask + I/O-bound work)
CMD ["gunicorn", "-w", "4", "-k", "gthread", "--threads", "8", "-b", "0.0.0.0:3000", "wsgi:app"]
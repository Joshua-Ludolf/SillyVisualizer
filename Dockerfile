# Use an official Python runtime as a parent image
FROM python:alpine3.21

# Update OS packages to address known vulnerabilities
RUN apk update && apk upgrade && rm -rf /var/cache/apk/*

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 3000 available to the world outside this container
EXPOSE 3000

# Define environment variable
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "main.py"]
# Use an official Python runtime as a parent image
FROM python:3.10-slim

RUN apt-get update && apt-get install -y git

# Set the working directory to /app
WORKDIR /app

# Copy the web app files from the "web_app" folder into the container
COPY web_app/ /app

# Install any dependencies required by your web app
RUN pip install -r requirements.txt

# Copy the custom library from the repository root into the container
COPY custom_lib /app/custom_lib

# Expose the port on which your web app listens
EXPOSE 5000

USER root

ENV FLASK_ENV=production

# Define the command to run your web app
CMD ["flask", "run", "--host=0.0.0.0"]
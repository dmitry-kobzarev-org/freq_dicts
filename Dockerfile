# Use an official Python runtime as a parent image
FROM python:3.10-slim

RUN apt-get update && apt-get install -y git

# Set the working directory to /app
WORKDIR /app

RUN python -m venv venv
RUN /bin/bash -c "source venv/bin/activate"

# Install any dependencies required by your web app
USER root

COPY web_app/requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY web_app/ /app
COPY custom_lib /app/custom_lib
COPY .dk_google /app/.dk_google

# Expose the port on which your web app listens
EXPOSE 5000



ENV FLASK_ENV=production
ENV ROOT_FULL_PATH=/app

# Define the command to run your web app
CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]
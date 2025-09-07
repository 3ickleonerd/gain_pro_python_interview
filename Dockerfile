# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /

# Copy everything into the container
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 8000

# Set the entrypoint to our new script
ENTRYPOINT ["fastapi", "run"]

# Command to run the application (will be overridden by docker-compose)
CMD ["--host", "0.0.0.0", "--port", "8000"]
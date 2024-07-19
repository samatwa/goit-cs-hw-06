# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the application files
COPY . /app

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose the ports for the HTTP server and socket server
EXPOSE 3000
EXPOSE 5000

# Run the main script
CMD ["python", "main.py"]
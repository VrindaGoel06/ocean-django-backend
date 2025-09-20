# Stage 1: Base build stage
FROM python:3.13.7-trixie AS builder
 
# Create the app directory
RUN mkdir /app
 
# Set the working directory
WORKDIR /app
 
# Set environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 

# Copy application code
COPY . .

# Install deps
RUN apt-get update
RUN apt-get install binutils libproj-dev gdal-bin -y

RUN useradd -m -r appuser && \
   chown -R appuser /app
   
# Switch to non-root user
USER appuser

ENV PATH="$PATH:/home/appuser/.local/bin"

RUN echo $PATH

# Install poetry
RUN pip install poetry

# Install Python dependencies
RUN poetry install
 
# Expose the application port
EXPOSE 8000
 
# Make the script executable
RUN chmod +x /app/entrypoint.sh

# Start the application
CMD ["/app/entrypoint.sh"]

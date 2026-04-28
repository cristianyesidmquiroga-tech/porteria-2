FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

WORKDIR /app

# Install dependencies
COPY carnet-sena/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY carnet-sena/ .

# Expose port 5000
EXPOSE 5000

# Run the application using the built-in Flask server
CMD ["python", "run.py"]

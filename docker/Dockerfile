
FROM python:3.12-slim

# Working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y && apt-get clean

# Copy the requirements file into the container
COPY ../requirements.txt /app/

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

# Run the application
CMD ["uvicorn", "app:app", "--reload", "--host", "0.0.0.0", "--port", "5000"]

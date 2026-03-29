# Use the official Python 3.11 image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port FastAPI runs on
EXPOSE 7860
EXPOSE 7860

# Command to run the application using Uvicorn
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "7860"]
# Backend stage
FROM python:3.10-slim AS backend

WORKDIR /app

# Install FFmpeg for Whisper
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code and .env
COPY backend/main.py .
COPY backend/.env .env

# Expose port
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Frontend stage
FROM node:16 AS frontend

WORKDIR /app

# Copy frontend package.json and install dependencies
COPY frontend/package.json .
COPY frontend/tailwind.config.js .
RUN npm install

# Copy frontend code
COPY frontend/src ./src
COPY frontend/public ./public

# Build frontend
RUN npm run build

# Expose the port your app runs on
EXPOSE 3000
 
# Define the command to run your app
CMD ["npm", "start"]
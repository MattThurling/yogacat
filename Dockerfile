# --- Node.js build stage ---
    FROM node:20-alpine AS node-builder

    # Set working directory for frontend
    WORKDIR /app/frontend
    
    # Install npm dependencies
    COPY frontend/package.json frontend/package-lock.json ./
    RUN npm install
    
    # Copy frontend files
    COPY frontend/ .
    
    # Build frontend assets (vite build outputs to ../static/dist)
    RUN npm run build
    
    # --- Final Python stage ---
    FROM python:3.10-slim
    
    # Set working directory
    WORKDIR /app
    
    # Install Python dependencies
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt gunicorn
    
    # Copy Django project files
    COPY . .
    
    # Copy frontend static files correctly from Vite build location
    COPY --from=node-builder /app/static/dist ./static/dist
    
    # Set environment variables
    ENV PYTHONUNBUFFERED=1
    ENV PORT=8080
    
    # Collect static files
    RUN python manage.py collectstatic --noinput
    
    # Start Django server with Gunicorn
    CMD ["gunicorn", "--bind", "0.0.0.0:8080", "YogaCat.wsgi:application"]
    

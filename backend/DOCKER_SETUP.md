# Docker Setup for Backend

This guide explains how to build and run the backend application using Docker.

## Files Created

- `Dockerfile` - Multi-stage Docker build configuration
- `.dockerignore` - Excludes unnecessary files from Docker build context
- `docker-compose.yml` - Docker Compose configuration with environment variables

## Prerequisites

1. Docker and Docker Compose installed
2. Environment variables configured (see below)

## Environment Variables

Create a `.env` file in the backend directory with the following variables:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o

# Firebase Configuration
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_PRIVATE_KEY_ID=your_firebase_private_key_id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nyour_firebase_private_key_here\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your_firebase_client_email
FIREBASE_CLIENT_ID=your_firebase_client_id
FIREBASE_CLIENT_X509_CERT_URL=your_firebase_client_cert_url
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_AUTH_DOMAIN=your_project_id.firebaseapp.com
FIREBASE_STORAGE_BUCKET=your_project_id.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_messaging_sender_id
FIREBASE_APP_ID=your_firebase_app_id
DATABASE_URL=your_database_url

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
GOOGLE_APPLICATION_CREDENTIALS=/app/serviceAccountKey.json

# Application Configuration
DEBUG=false
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://localhost:8501
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=Authorization,Content-Type,Accept,Origin,User-Agent
CORS_EXPOSE_HEADERS=Content-Length,Content-Range
CORS_MAX_AGE=3600
```

## Running with Docker Compose (Recommended)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create your `.env` file with the required environment variables

3. Build and run the container:
   ```bash
   docker-compose up --build
   ```

4. The API will be available at `http://localhost:8000`

## Running with Docker only

1. Build the image:
   ```bash
   docker build -t creators-copilot-backend .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 --env-file .env creators-copilot-backend
   ```

## Firebase Service Account (Optional)

If you prefer to use a Firebase service account JSON file instead of environment variables:

1. Place your `serviceAccountKey.json` file in the backend directory
2. Uncomment the volume mount in `docker-compose.yml`:
   ```yaml
   - ./serviceAccountKey.json:/app/serviceAccountKey.json:ro
   ```
3. Set `GOOGLE_APPLICATION_CREDENTIALS=/app/serviceAccountKey.json` in your `.env`

## Health Check

The container includes a health check that monitors the `/health` endpoint. You can check the health status:

```bash
docker ps  # Look for health status in the STATUS column
```

## Development

For development with hot reloading, you can mount the source code:

```yaml
volumes:
  - ./app:/app/app:ro  # Mount source code for development
```

And set `DEBUG=true` in your environment variables.

## Troubleshooting

1. **Port conflicts**: If port 8000 is in use, change the port mapping in docker-compose.yml
2. **Environment variables**: Ensure all required variables are set in your `.env` file
3. **Firebase auth**: Verify your Firebase configuration is correct
4. **Build failures**: Check that all dependencies in requirements.txt are compatible

## API Endpoints

Once running, you can access:
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`
- Root endpoint: `http://localhost:8000/`
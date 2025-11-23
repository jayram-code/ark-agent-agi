#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-your-gcp-project}"
IMAGE_NAME="${IMAGE_NAME:-gcr.io/$PROJECT_ID/ark-agent-agi:latest}"
REGION="${REGION:-us-central1}"
GCS_BUCKET="${GCS_BUCKET:-YOUR_BUCKET_NAME}"
GCS_PREFIX="${GCS_PREFIX:-ark-agent}"

# build and push image (uses Cloud Build)
echo "Building and pushing image to $IMAGE_NAME"
gcloud builds submit --tag "$IMAGE_NAME"

# deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ark-agent-agi \
  --image "$IMAGE_NAME" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars "GCS_BUCKET=$GCS_BUCKET,GCS_PREFIX=$GCS_PREFIX,GOOGLE_API_KEY=${GOOGLE_API_KEY:-},GEMINI_FLASH_MODEL=${GEMINI_FLASH_MODEL:-},GEMINI_PRO_MODEL=${GEMINI_PRO_MODEL:-}"

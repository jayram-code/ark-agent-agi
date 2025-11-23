#!/usr/bin/env bash
set -euo pipefail
BUCKET=${BUCKET:-YOUR_BUCKET_NAME}
PREFIX=${PREFIX:-ark-agent}
# upload models directory
if [ -d "src/models" ]; then
    gsutil -m cp -r src/models gs://$BUCKET/$PREFIX/models
fi
# upload runtime DB (example)
if [ -d "runtime" ]; then
    gsutil -m cp -r runtime/* gs://$BUCKET/$PREFIX/db || true
fi
# upload kb docs
if [ -d "data/kb_docs" ]; then
    gsutil -m cp -r data/kb_docs gs://$BUCKET/$PREFIX/kb_docs || true
fi

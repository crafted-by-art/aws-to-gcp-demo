# tag-service

GCP Cloud Function for tag-service

## Deploy
```bash
gcloud functions deploy tag-service --gen2 --runtime=python311 --region=us-central1 --source=. --entry-point=tag_service --trigger-http --allow-unauthenticated
```

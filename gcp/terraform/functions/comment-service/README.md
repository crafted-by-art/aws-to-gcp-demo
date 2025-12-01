# comment-service

GCP Cloud Function for comment-service

## Deploy
```bash
gcloud functions deploy comment-service --gen2 --runtime=python311 --region=us-central1 --source=. --entry-point=comment_service --trigger-http --allow-unauthenticated
```

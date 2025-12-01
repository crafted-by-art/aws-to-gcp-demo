# profile-service

GCP Cloud Function for profile-service

## Deploy
```bash
gcloud functions deploy profile-service --gen2 --runtime=python311 --region=us-central1 --source=. --entry-point=profile_service --trigger-http --allow-unauthenticated
```

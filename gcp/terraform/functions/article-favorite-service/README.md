# article-favorite-service

GCP Cloud Function for article-favorite-service

## Deploy
```bash
gcloud functions deploy article-favorite-service --gen2 --runtime=python311 --region=us-central1 --source=. --entry-point=article_favorite_service --trigger-http --allow-unauthenticated
```

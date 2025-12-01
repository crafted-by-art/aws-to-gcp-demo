# Authentication Service - GCP Version

## Status
⚠️ COPIED FROM AWS - Needs transformation

## Files
- main.py (13K) - AWS Lambda code (needs GCP transformation)
- requirements.txt (85B) - GCP dependencies ready

## Key Changes Needed
1. Replace boto3 with google-cloud-firestore
2. Update DynamoDB operations to Firestore
3. Change Lambda event handler to Cloud Functions request handler
4. Update response format

See parent directory for transformation guide.

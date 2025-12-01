# Terraform Apply Issues - Analysis

## Issue #1: IAM Permissions ✅ FIXED

### Errors:
- Error 403: Permission 'apigateway.apis.create' denied
- Error 403: Firestore database creation denied  
- Error 403: Policy update access denied

### Solution Applied:
Added missing roles to codemie-migration-sa:
- roles/apigateway.admin
- roles/datastore.owner
- roles/resourcemanager.projectIamAdmin

## Issue #2: Cloud Functions Failed 🔧 NEEDS FIX

### Error:
Container Healthcheck failed - functions not listening on PORT=8080

### Root Cause:
Functions contain AWS Lambda code, not GCP Cloud Functions code

### Evidence:
- Uses boto3 (AWS SDK) instead of google-cloud-firestore
- Uses lambda_handler() instead of main()
- Uses DynamoDB instead of Firestore
- Missing functions-framework dependency

### Required Fix:
Rewrite functions for GCP Cloud Functions Gen 2 format

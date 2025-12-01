# AWS CloudFormation Master Stack Deployment Guide

@overview
This repository contains a modular, production-grade AWS CloudFormation architecture for deploying a multi-service application. The stack is designed for maximum flexibility, maintainability, and clear separation of concerns. Each AWS service and Lambda function is defined in its own CloudFormation template, and all are orchestrated by a root (master) stack.

## Discovered Resources
- ** Services:** 
  - IAM
  - VPC
  - S3
  - Lambda (shared resources)
  - DynamoDB
  - CloudWatch
  - API Gateway
- **Lambda Functions:*
  - django-rest-pet-clinic-article-favorite-service-dev
  - django-rest-pet-clinic-authentication-service-dev
  - django-rest-pet-clinic-comment-service-dev
  - django-rest-pet-clinic-tag-service-dev
  - django-rest-pet-clinic-article-feed-service-dev
  - django-rest-pet-clinic-article-service-dev
  - django-rest-pet-clinic-profile-service-dev

## CloudFormation Templates

`aws/*.yaml`
- `aws/iam.yaml`
[ aws/vpc.yaml`
- `aws/s3.yaml`
- `aws/lambda.yaml`
- `aws/dynamodb.yaml` (if present)
- `aws/cloudwatch.yaml`
- `aws/apigateway.yaml`

`aws/lambdas/*.yaml`
- `aws/lambdas/django-rest-pet-clinic-article-favorite-service-dev.yaml`
- `aws/lambdas/django-rest-pet-clinic-authentication-service-dev.yaml`
- `aws/lambdas/django-rest-pet-clinic-comment-service-dev.yaml`
- `aws/lambdas/django-rest-pet-clinic-tag-service-dev.yaml`
- `aws/lambdas/django-rest-pet-clinic-article-feed-service-dev.yaml`
- `aws/lambdas/django-rest-pet-clinic-article-service-dev.yaml`
- `aws/lambdas/django-rest-pet-clinic-profile-service-dev.yaml`

## Architecture Explanation
- **Root Stack:** Orchestrates all service and Lambda stacks as nested stacks.
- **Service Stacks:** Each AWS service (IAM, VPC, etc.) is defined in its own template for modularity.
- **Lambda Stacks:** Each Lambda function is deployed via its own nested stack, allowing independent updates and rollbacks.
- **Dependency Management:**
  - IAM stack is deployed first (provides roles/policies).
  - VPC and S3 depend on IAM.
  - Lambda stacks depend on IAM and VPC.
  - API Gateway depends on IAM and VPC.
- **Update Independence:** Individual Lambda stacks can be updated or rolled without affecting other functions or core infrastructure.

## Deployment Instructions

### 1. Upload Templates to S3

- **Service templates:** Upload all `aws/*.yaml` files to `s3 <your-bucket>/aws`/`
- **Lambda templates:** Upload all `aws/lambdas/*.yaml` files to `s3 <your-bucket>/aws/lambdas/`/`

Example using AWS CLI:

``ash 
aws s3 cr aws/ s3://<your-bucket>/aws/ -recursive --exclude "lambdas/*"
aws s3 cr aws/lambdas/ s3://<your-bucket>/aws/lambdas/ --recursive

`
[## 2. Deploy the Root Stack](https://s3.amazonaws.com/<your-bucket>/aws/root-stack.yaml)
You can deploy the root stack using the AWS Console or CLI.The root stack will reference all nested stacks.

Example CLIcommand:

``ash 
aws cloudformation create-stack \
  --stack-name root-stack \
  --template-url https://s3.amazonaws.com/<your-bucket>/aws/root-stack.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters ParameterKey=TemplatesBucketName,ParameterValue=<your-bucket> \
            ParameterKey=TemplatesBucketPrefix,ParameterValue=aws \
            ParameterKey=Environment,ParameterValue=dev
```

### 3. Monitor Nested Stack Creation
- Use the AWS CloudFormation Console to monitor the progress of the root stack and all nested stacks.
- Ensure all stacks reach "CREATE_COMPLETE" status.

### 4. Verify Lambda Function Stacks
- Each Lambda function is deployed as its own stack under the root stack.
- You can update or rollback individual Lambda stacks as needed without redeploying the entire application.

## Benefits of Individual Lambda Stacks
- *INDEPENDENT Deployment:* Update or rollback a single Lambda function without affecting others.
- **Separation of Concerns:** Each function's infrastructure is isolated.
- **Easier Rollback:** Rollback only the affected Lambda stack if an issue occurs.
- **Clear Change Tracking.** Each function's changes are tracked in its own template and stack events.

## Troubleshooting Tips
- **Stack Fails to Create:** 
  - Check IAM permissions for CloudFormation and S3 access.
  - Ensure all template URLs
  - Review the Events tab in the CloudFormation Console for error messages.
- **Lambda Function Fails to Deploy:** 
  - Check the Lambda stack events for errors (e.g., missing IAM roles, VPC config).
  - Ensure all dependencies (IAM,  VPC) are created successfully.
- **Parameter Issues:** 
  - Make sure you pass the correct parameters (bucket name, prefix, environment) when deploying the root stack.

## Example AWS CLI Commands

*Update a Lambda Stack:**
```ash 
aws cloudformation update-stack \
  --stack-name root-stack-LambdaDjangoRestPetClinicArticleServiceDevStack-<uniqueid> \
  --template-url https://s3.amazonaws.com/<your-bucket>/aws/lambdas/django-rest-pet-clinic-article-service-dev.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters ParameterKey=Environment,ParameterValue=dev
```

*Rollback a Lambda Stack:** 
```ash
aws cloudformation rollback-stack --stack-name <lambda-stack-name>
```

*Delete the Entire Stack:** 
```ash
aws cloudformation delete-stack --stack-name root-stack
```

---

**Branch:** aws-to-cf-20

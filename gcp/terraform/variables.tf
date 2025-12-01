# GCP Variables
# Equivalent to AWS variables

variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "aap-aws-gcp-migration-demo"
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "django-rest-pet-clinic"
}

variable "jwt_secret" {
  description = "JWT secret key for authentication"
  type        = string
  default     = "your-secret-key-change-in-production"
  sensitive   = true
}

variable "log_retention_days" {
  description = "Number of days to retain logs"
  type        = number
  default     = 7
}

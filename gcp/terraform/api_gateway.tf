# API Gateway Configuration
# Equivalent to AWS API Gateway

# Enable API Gateway API
resource "google_project_service" "apigateway" {
  service            = "apigateway.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "servicecontrol" {
  service            = "servicecontrol.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "servicemanagement" {
  service            = "servicemanagement.googleapis.com"
  disable_on_destroy = false
}

# API Gateway API
resource "google_api_gateway_api" "pet_clinic_api" {
  provider = google-beta
  api_id       = "pet-clinic-api"
  display_name = "Django Pet Clinic API"

  labels = {
    environment = var.environment
    project     = var.project_name
    managed_by  = "terraform"
  }

  depends_on = [google_project_service.apigateway]
}

# Note: API Gateway in GCP requires OpenAPI specification
# This will be configured separately or with Cloud Endpoints
# Alternative: Use Cloud Run with direct HTTPS endpoints

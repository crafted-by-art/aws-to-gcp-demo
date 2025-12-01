# Cloud Logging Configuration
# Equivalent to AWS CloudWatch Logs

resource "google_project_service" "logging" {
  service            = "logging.googleapis.com"
  disable_on_destroy = false
}

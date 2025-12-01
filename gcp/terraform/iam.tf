# IAM Configuration
# Equivalent to AWS IAM roles and policies

# Service Account for Cloud Functions
resource "google_service_account" "cloud_function_sa" {
  account_id   = "pet-clinic-functions"
  display_name = "Cloud Functions Service Account"
  description  = "Service account for Django Pet Clinic Cloud Functions"
}

# Grant Firestore access to service account
resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.cloud_function_sa.email}"
}

# Grant Cloud Logging access
resource "google_project_iam_member" "logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cloud_function_sa.email}"
}

# Grant Storage access for function deployments
resource "google_project_iam_member" "storage_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.cloud_function_sa.email}"
}

# Grant Cloud Trace access for tracing
resource "google_project_iam_member" "trace_agent" {
  project = var.project_id
  role    = "roles/cloudtrace.agent"
  member  = "serviceAccount:${google_service_account.cloud_function_sa.email}"
}

# Grant Monitoring Metric Writer
resource "google_project_iam_member" "monitoring_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.cloud_function_sa.email}"
}

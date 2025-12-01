# Cloud Storage Buckets
# Equivalent to AWS S3 buckets

# Enable Cloud Storage API
resource "google_project_service" "storage" {
  service            = "storage.googleapis.com"
  disable_on_destroy = false
}

# Cloud Functions deployment artifacts bucket
resource "google_storage_bucket" "function_deployments" {
  name          = "${var.project_id}-function-deployments-${var.environment}"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      num_newer_versions = 3
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = var.environment
    project     = var.project_name
    managed_by  = "terraform"
  }

  depends_on = [google_project_service.storage]
}

# Application logs bucket
resource "google_storage_bucket" "application_logs" {
  name          = "${var.project_id}-application-logs-${var.environment}"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  labels = {
    environment = var.environment
    project     = var.project_name
    managed_by  = "terraform"
  }

  depends_on = [google_project_service.storage]
}

# Firestore backups bucket
resource "google_storage_bucket" "firestore_backups" {
  name          = "${var.project_id}-firestore-backups-${var.environment}"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = 180
    }
    action {
      type          = "SetStorageClass"
      storage_class = "ARCHIVE"
    }
  }

  labels = {
    environment = var.environment
    project     = var.project_name
    managed_by  = "terraform"
  }

  depends_on = [google_project_service.storage]
}

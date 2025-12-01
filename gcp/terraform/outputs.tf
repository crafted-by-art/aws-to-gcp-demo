# Output Values
# Equivalent to AWS outputs

output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP Region"
  value       = var.region
}

output "firestore_database" {
  description = "Firestore Database ID"
  value       = google_firestore_database.database.name
}

output "service_account_email" {
  description = "Cloud Functions Service Account Email"
  value       = google_service_account.cloud_function_sa.email
}

output "function_urls" {
  description = "Cloud Function URLs"
  value = {
    authentication   = google_cloudfunctions2_function.authentication_service.service_config[0].uri
    article          = google_cloudfunctions2_function.article_service.service_config[0].uri
    article_feed     = google_cloudfunctions2_function.article_feed_service.service_config[0].uri
    article_favorite = google_cloudfunctions2_function.article_favorite_service.service_config[0].uri
    comment          = google_cloudfunctions2_function.comment_service.service_config[0].uri
    profile          = google_cloudfunctions2_function.profile_service.service_config[0].uri
    tag              = google_cloudfunctions2_function.tag_service.service_config[0].uri
  }
}

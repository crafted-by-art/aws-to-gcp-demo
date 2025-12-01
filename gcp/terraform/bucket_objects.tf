# Storage Bucket Objects for Function Deployment Packages
# These upload the local ZIP files to Cloud Storage

resource "google_storage_bucket_object" "authentication_service_zip" {
  name   = "authentication-service.zip"
  bucket = google_storage_bucket.function_deployments.name
  source = "${path.module}/functions/authentication-service.zip"
}

resource "google_storage_bucket_object" "article_service_zip" {
  name   = "article-service.zip"
  bucket = google_storage_bucket.function_deployments.name
  source = "${path.module}/functions/article-service.zip"
}

resource "google_storage_bucket_object" "article_feed_service_zip" {
  name   = "article-feed-service.zip"
  bucket = google_storage_bucket.function_deployments.name
  source = "${path.module}/functions/article-feed-service.zip"
}

resource "google_storage_bucket_object" "article_favorite_service_zip" {
  name   = "article-favorite-service.zip"
  bucket = google_storage_bucket.function_deployments.name
  source = "${path.module}/functions/article-favorite-service.zip"
}

resource "google_storage_bucket_object" "comment_service_zip" {
  name   = "comment-service.zip"
  bucket = google_storage_bucket.function_deployments.name
  source = "${path.module}/functions/comment-service.zip"
}

resource "google_storage_bucket_object" "profile_service_zip" {
  name   = "profile-service.zip"
  bucket = google_storage_bucket.function_deployments.name
  source = "${path.module}/functions/profile-service.zip"
}

resource "google_storage_bucket_object" "tag_service_zip" {
  name   = "tag-service.zip"
  bucket = google_storage_bucket.function_deployments.name
  source = "${path.module}/functions/tag-service.zip"
}

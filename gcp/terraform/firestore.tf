# Firestore Database Configuration
# Equivalent to AWS DynamoDB tables

# Enable Firestore API
resource "google_project_service" "firestore" {
  service            = "firestore.googleapis.com"
  disable_on_destroy = false
}

# Firestore Database in Native mode
resource "google_firestore_database" "database" {
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
  depends_on  = [google_project_service.firestore]
}

# Firestore indexes for Users collection
resource "google_firestore_index" "users_email" {
  collection = "Users"
  fields {
    field_path = "email"
    order      = "ASCENDING"
  }
  fields {
    field_path = "__name__"
    order      = "ASCENDING"
  }
  depends_on = [google_firestore_database.database]
}

resource "google_firestore_index" "users_username" {
  collection = "Users"
  fields {
    field_path = "username"
    order      = "ASCENDING"
  }
  fields {
    field_path = "__name__"
    order      = "ASCENDING"
  }
  depends_on = [google_firestore_database.database]
}

# Profiles indexes
resource "google_firestore_index" "profiles_username" {
  collection = "Profiles"
  fields {
    field_path = "username"
    order      = "ASCENDING"
  }
  fields {
    field_path = "__name__"
    order      = "ASCENDING"
  }
  depends_on = [google_firestore_database.database]
}

resource "google_firestore_index" "profiles_user_id" {
  collection = "Profiles"
  fields {
    field_path = "user_id"
    order      = "ASCENDING"
  }
  fields {
    field_path = "__name__"
    order      = "ASCENDING"
  }
  depends_on = [google_firestore_database.database]
}

# Articles indexes
resource "google_firestore_index" "articles_author_id" {
  collection = "Articles"
  fields {
    field_path = "author_id"
    order      = "ASCENDING"
  }
  fields {
    field_path = "createdAt"
    order      = "DESCENDING"
  }
  depends_on = [google_firestore_database.database]
}

# Comments indexes
resource "google_firestore_index" "comments_article_slug" {
  collection = "Comments"
  fields {
    field_path = "article_slug"
    order      = "ASCENDING"
  }
  fields {
    field_path = "createdAt"
    order      = "DESCENDING"
  }
  depends_on = [google_firestore_database.database]
}

# Follows indexes
resource "google_firestore_index" "follows_follower_id" {
  collection = "Follows"
  fields {
    field_path = "follower_id"
    order      = "ASCENDING"
  }
  fields {
    field_path = "followed_id"
    order      = "ASCENDING"
  }
  depends_on = [google_firestore_database.database]
}

# ArticleFavorites indexes
resource "google_firestore_index" "favorites_article_slug" {
  collection = "ArticleFavorites"
  fields {
    field_path = "article_slug"
    order      = "ASCENDING"
  }
  fields {
    field_path = "username"
    order      = "ASCENDING"
  }
  depends_on = [google_firestore_database.database]
}

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "mock-trail-project-1"
}

variable "region" {
  description = "GCP Region for resources"
  type        = string
  default     = "asia-south1"
}

variable "bucket_name" {
  description = "GCS Bucket Name for Raw Data Lake"
  type        = string
  default     = "mock-project-bucket-surya"
}

# GCS Bucket for Bronze Data Lake
resource "google_storage_bucket" "raw_data_lake" {
  name          = var.bucket_name
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}

# BigQuery Bronze Dataset
resource "google_bigquery_dataset" "bronze" {
  dataset_id  = "bronze"
  description = "Bronze Layer - Raw Ingested Data"
  location    = var.region
}

# BigQuery Silver Dataset
resource "google_bigquery_dataset" "silver" {
  dataset_id  = "silver"
  description = "Silver Layer - Cleaned & Enriched Datasets"
  location    = var.region
}

# BigQuery Gold Dataset
resource "google_bigquery_dataset" "gold" {
  dataset_id  = "gold"
  description = "Gold Layer - Dimensional Star Schema & Aggregations"
  location    = var.region
}

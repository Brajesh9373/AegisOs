variable "kubeconfig_path" {
  description = "Path to the kubeconfig file used to reach the cluster."
  type        = string
  default     = "~/.kube/config"
}

variable "namespace" {
  description = "Kubernetes namespace for the ECMS platform."
  type        = string
  default     = "ecms"
}

variable "environment" {
  description = "Deployment environment (development, testing, staging, production)."
  type        = string
  default     = "production"
}

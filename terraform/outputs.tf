output "namespace" {
  description = "The ECMS Kubernetes namespace."
  value       = kubernetes_namespace.ecms.metadata[0].name
}

output "backend_config_map" {
  description = "The name of the backend ConfigMap."
  value       = kubernetes_config_map.backend.metadata[0].name
}

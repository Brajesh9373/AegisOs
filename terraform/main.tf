provider "kubernetes" {
  config_path = var.kubeconfig_path
}

resource "kubernetes_namespace" "ecms" {
  metadata {
    name = var.namespace

    labels = {
      "app.kubernetes.io/name" = "ecms"
      "environment"            = var.environment
    }
  }
}

resource "kubernetes_config_map" "backend" {
  metadata {
    name      = "ecms-backend-config"
    namespace = kubernetes_namespace.ecms.metadata[0].name
  }

  data = {
    ECMS_ENVIRONMENT = var.environment
    ECMS_LOG_LEVEL   = "INFO"
  }
}

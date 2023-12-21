provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "sean_gpt_rg" {
  name     = "sean-gpt-rg"
  location = "East US"
}

resource "azurerm_kubernetes_cluster" "sean_gpt_aks" {
  name                = "sean-gpt-aks"
  location            = azurerm_resource_group.sean_gpt_rg.location
  resource_group_name = azurerm_resource_group.sean_gpt_rg.name
  dns_prefix          = "sean-gpt-k8s"

  default_node_pool {
    name       = "default"
    node_count = 1
    vm_size    = "Standard_DS2_v2"
  }

  identity {
    type = "SystemAssigned"
  }
}

output "kube_config" {
  value       = azurerm_kubernetes_cluster.sean_gpt_aks.kube_config_raw
  description = "Kubernetes configuration file for kubectl access"
  sensitive   = true
}
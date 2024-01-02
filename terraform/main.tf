provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "sean_gpt_rg" {
  name     = "sean-gpt-rg"
  location = "East US"
}

resource "azurerm_container_registry" "acr" {
  name                     = "seangptacr${random_string.acr_suffix.result}"
  resource_group_name      = azurerm_resource_group.sean_gpt_rg.name
  location                 = azurerm_resource_group.sean_gpt_rg.location
  sku                      = "Basic"  # or Standard, Premium
  admin_enabled            = false
}

resource "random_string" "acr_suffix" {
  length  = 6
  special = false
  upper   = false
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

  depends_on = [
    azurerm_container_registry.acr
  ]
}

resource "azurerm_role_assignment" "aks_acr_pull" {
  scope                = azurerm_container_registry.acr.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.sean_gpt_aks.kubelet_identity[0].object_id

  depends_on = [
    azurerm_kubernetes_cluster.sean_gpt_aks,
    azurerm_container_registry.acr
  ]
}

resource "null_resource" "configure_kubectl_context" {
  depends_on = [azurerm_kubernetes_cluster.sean_gpt_aks]

  provisioner "local-exec" {
    command = <<EOT
      echo '${azurerm_kubernetes_cluster.sean_gpt_aks.kube_config_raw}' > ~/.kube/sean-gpt-config
      export KUBECONFIG=~/.kube/sean-gpt-config:~/.kube/config
      kubectl config view --merge --flatten > ~/.kube/merged_config
      cat ~/.kube/sean-gpt-config | gh secret set KUBECONFIG -Rmrplants/sean_gpt
      mv ~/.kube/merged_config ~/.kube/config
      rm ~/.kube/sean-gpt-config
    EOT
  }
}

resource "null_resource" "cleanup_kubectl_context" {
  depends_on = [azurerm_kubernetes_cluster.sean_gpt_aks]

  provisioner "local-exec" {
    when    = destroy
    command = "kubectl config delete-context sean-gpt-aks"
  }
}

output "acr_name" {
  value = azurerm_container_registry.acr.name
  description = "The name of the Azure Container Registry."
}

output "acr_login_server" {
  value = azurerm_container_registry.acr.login_server
  description = "The login server URL of the Azure Container Registry."
}
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
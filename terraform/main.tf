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
    enable_auto_scaling = true
    min_count = 1
    max_count = 2
    vm_size    = "Standard_DS2_v2"
  }

  identity {
    type = "SystemAssigned"
  }

}

resource "azurerm_kubernetes_cluster_node_pool" "gpu_node_pool" {
  name                  = "gpunodepool"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.sean_gpt_aks.id
  vm_size               = "Standard_NC4as_T4_v3"
  node_count            = 0
  min_count             = 0
  max_count             = 10
  enable_auto_scaling   = true
  os_disk_size_gb       = 30
  node_taints = ["nvidia.com/gpu=present:NoSchedule"]
  node_labels = {
    "gpu" = "nvidia"
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
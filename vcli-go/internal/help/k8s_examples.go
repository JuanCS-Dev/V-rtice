package help

// K8sGetExamples provides examples for k8s get command
var K8sGetExamples = ExampleGroup{
	Title: "Get Resources",
	Examples: []Example{
		{
			Description: "List all pods in default namespace",
			Command:     "vcli k8s get pods",
		},
		{
			Description: "List pods in specific namespace",
			Command:     "vcli k8s get pods --namespace kube-system",
		},
		{
			Description: "List pods across all namespaces",
			Command:     "vcli k8s get pods --all-namespaces",
		},
		{
			Description: "Get pods in JSON format",
			Command:     "vcli k8s get pods --output json",
		},
		{
			Description: "Get single pod details",
			Command:     "vcli k8s get pod nginx-7848d4b86f-9xvzk",
		},
	},
}

// K8sGetNodesExamples provides examples for getting nodes
var K8sGetNodesExamples = ExampleGroup{
	Title: "Get Nodes",
	Examples: []Example{
		{
			Description: "List all nodes",
			Command:     "vcli k8s get nodes",
		},
		{
			Description: "Get node details in YAML",
			Command:     "vcli k8s get node worker-1 --output yaml",
		},
		{
			Description: "List nodes with labels",
			Command:     "vcli k8s get nodes --show-labels",
		},
	},
}

// K8sLogsExamples provides examples for logs command
var K8sLogsExamples = ExampleGroup{
	Title: "View Logs",
	Examples: []Example{
		{
			Description: "View pod logs",
			Command:     "vcli k8s logs nginx-pod",
		},
		{
			Description: "Follow logs in real-time",
			Command:     "vcli k8s logs nginx-pod --follow",
		},
		{
			Description: "View logs from specific container",
			Command:     "vcli k8s logs nginx-pod --container sidecar",
		},
		{
			Description: "View last 50 lines",
			Command:     "vcli k8s logs nginx-pod --tail 50",
		},
		{
			Description: "View logs since timestamp",
			Command:     "vcli k8s logs nginx-pod --since-time=2025-10-22T10:00:00Z",
		},
	},
}

// K8sApplyExamples provides examples for apply command
var K8sApplyExamples = ExampleGroup{
	Title: "Apply Configuration",
	Examples: []Example{
		{
			Description: "Apply configuration from file",
			Command:     "vcli k8s apply -f deployment.yaml",
		},
		{
			Description: "Apply multiple files",
			Command:     "vcli k8s apply -f deployment.yaml -f service.yaml",
		},
		{
			Description: "Apply all files in directory",
			Command:     "vcli k8s apply -f ./manifests/",
		},
		{
			Description: "Apply with dry-run",
			Command:     "vcli k8s apply -f deployment.yaml --dry-run",
		},
	},
}

// K8sDeleteExamples provides examples for delete command
var K8sDeleteExamples = ExampleGroup{
	Title: "Delete Resources",
	Examples: []Example{
		{
			Description: "Delete a pod",
			Command:     "vcli k8s delete pod nginx-pod",
		},
		{
			Description: "Delete from file",
			Command:     "vcli k8s delete -f deployment.yaml",
		},
		{
			Description: "Delete all pods in namespace",
			Command:     "vcli k8s delete pods --all --namespace dev",
		},
		{
			Description: "Force delete a pod",
			Command:     "vcli k8s delete pod nginx-pod --force --grace-period=0",
		},
	},
}

// K8sScaleExamples provides examples for scale command
var K8sScaleExamples = ExampleGroup{
	Title: "Scale Resources",
	Examples: []Example{
		{
			Description: "Scale deployment to 3 replicas",
			Command:     "vcli k8s scale deployment nginx --replicas=3",
		},
		{
			Description: "Scale deployment in specific namespace",
			Command:     "vcli k8s scale deployment api --replicas=5 --namespace production",
		},
		{
			Description: "Scale StatefulSet",
			Command:     "vcli k8s scale statefulset database --replicas=3",
		},
	},
}

// K8sExecExamples provides examples for exec command
var K8sExecExamples = ExampleGroup{
	Title: "Execute Commands",
	Examples: []Example{
		{
			Description: "Execute bash shell in pod",
			Command:     "vcli k8s exec nginx-pod -- /bin/bash",
		},
		{
			Description: "Execute interactive shell",
			Command:     "vcli k8s exec -it nginx-pod -- sh",
		},
		{
			Description: "Execute command in specific container",
			Command:     "vcli k8s exec nginx-pod --container sidecar -- ls -la",
		},
		{
			Description: "Run one-off command",
			Command:     "vcli k8s exec nginx-pod -- curl localhost:8080/health",
		},
	},
}

// K8sPortForwardExamples provides examples for port-forward command
var K8sPortForwardExamples = ExampleGroup{
	Title: "Port Forwarding",
	Examples: []Example{
		{
			Description: "Forward local port 8080 to pod port 80",
			Command:     "vcli k8s port-forward nginx-pod 8080:80",
		},
		{
			Description: "Forward to service",
			Command:     "vcli k8s port-forward service/nginx 8080:80",
		},
		{
			Description: "Forward to deployment",
			Command:     "vcli k8s port-forward deployment/nginx 8080:80",
		},
		{
			Description: "Forward multiple ports",
			Command:     "vcli k8s port-forward nginx-pod 8080:80 8443:443",
		},
	},
}

// K8sDescribeExamples provides examples for describe command
var K8sDescribeExamples = ExampleGroup{
	Title: "Describe Resources",
	Examples: []Example{
		{
			Description: "Describe a pod",
			Command:     "vcli k8s describe pod nginx-pod",
		},
		{
			Description: "Describe a deployment",
			Command:     "vcli k8s describe deployment nginx",
		},
		{
			Description: "Describe a node",
			Command:     "vcli k8s describe node worker-1",
		},
		{
			Description: "Describe all pods in namespace",
			Command:     "vcli k8s describe pods --namespace kube-system",
		},
	},
}

// K8sRolloutExamples provides examples for rollout commands
var K8sRolloutExamples = ExampleGroup{
	Title: "Manage Rollouts",
	Examples: []Example{
		{
			Description: "Check rollout status",
			Command:     "vcli k8s rollout status deployment/nginx",
		},
		{
			Description: "View rollout history",
			Command:     "vcli k8s rollout history deployment/nginx",
		},
		{
			Description: "Undo last rollout",
			Command:     "vcli k8s rollout undo deployment/nginx",
		},
		{
			Description: "Restart deployment",
			Command:     "vcli k8s rollout restart deployment/nginx",
		},
		{
			Description: "Pause rollout",
			Command:     "vcli k8s rollout pause deployment/nginx",
		},
		{
			Description: "Resume rollout",
			Command:     "vcli k8s rollout resume deployment/nginx",
		},
	},
}

// K8sTopExamples provides examples for top/metrics commands
var K8sTopExamples = ExampleGroup{
	Title: "Resource Metrics",
	Examples: []Example{
		{
			Description: "Show node metrics",
			Command:     "vcli k8s top nodes",
		},
		{
			Description: "Show metrics for specific node",
			Command:     "vcli k8s top node worker-1",
		},
		{
			Description: "Show pod metrics",
			Command:     "vcli k8s top pods",
		},
		{
			Description: "Show pod metrics with container breakdown",
			Command:     "vcli k8s top pods --containers",
		},
		{
			Description: "Show metrics for specific pod",
			Command:     "vcli k8s top pod nginx-7848d4b86f-9xvzk --containers",
		},
	},
}

// K8sLabelExamples provides examples for label command
var K8sLabelExamples = ExampleGroup{
	Title: "Manage Labels",
	Examples: []Example{
		{
			Description: "Add label to pod",
			Command:     "vcli k8s label pod nginx-pod env=production",
		},
		{
			Description: "Add multiple labels",
			Command:     "vcli k8s label pod nginx-pod env=prod tier=frontend",
		},
		{
			Description: "Remove label",
			Command:     "vcli k8s label pod nginx-pod env-",
		},
		{
			Description: "Overwrite existing label",
			Command:     "vcli k8s label pod nginx-pod env=staging --overwrite",
		},
		{
			Description: "Label all pods in namespace",
			Command:     "vcli k8s label pods --all env=dev --namespace development",
		},
	},
}

// K8sAnnotateExamples provides examples for annotate command
var K8sAnnotateExamples = ExampleGroup{
	Title: "Manage Annotations",
	Examples: []Example{
		{
			Description: "Add annotation to service",
			Command:     "vcli k8s annotate service nginx description=\"Main web service\"",
		},
		{
			Description: "Add multiple annotations",
			Command:     "vcli k8s annotate pod nginx owner=team-a contact=ops@example.com",
		},
		{
			Description: "Remove annotation",
			Command:     "vcli k8s annotate service nginx description-",
		},
		{
			Description: "Overwrite annotation",
			Command:     "vcli k8s annotate pod nginx owner=team-b --overwrite",
		},
	},
}

// K8sAuthExamples provides examples for auth commands
var K8sAuthExamples = ExampleGroup{
	Title: "Authorization & Authentication",
	Examples: []Example{
		{
			Description: "Check if you can create pods",
			Command:     "vcli k8s auth can-i create pods",
		},
		{
			Description: "Check permission in specific namespace",
			Command:     "vcli k8s auth can-i delete deployments --namespace production",
		},
		{
			Description: "Check permission as different user",
			Command:     "vcli k8s auth can-i get secrets --as developer",
		},
		{
			Description: "Show current user info",
			Command:     "vcli k8s auth whoami",
		},
		{
			Description: "Show detailed auth info",
			Command:     "vcli k8s auth whoami --output json",
		},
	},
}

// K8sConfigMapExamples provides examples for ConfigMap operations
var K8sConfigMapExamples = ExampleGroup{
	Title: "ConfigMap Operations",
	Examples: []Example{
		{
			Description: "Create ConfigMap from literal values",
			Command:     "vcli k8s create configmap app-config --from-literal=key1=value1",
		},
		{
			Description: "Create ConfigMap from file",
			Command:     "vcli k8s create configmap app-config --from-file=config.properties",
		},
		{
			Description: "List all ConfigMaps",
			Command:     "vcli k8s get configmaps",
		},
		{
			Description: "Get ConfigMap in YAML",
			Command:     "vcli k8s get configmap app-config --output yaml",
		},
	},
}

// K8sSecretExamples provides examples for Secret operations
var K8sSecretExamples = ExampleGroup{
	Title: "Secret Operations",
	Examples: []Example{
		{
			Description: "Create generic secret",
			Command:     "vcli k8s create secret generic db-secret --from-literal=password=secret123",
		},
		{
			Description: "Create TLS secret",
			Command:     "vcli k8s create secret tls tls-secret --cert=tls.crt --key=tls.key",
		},
		{
			Description: "Create Docker registry secret",
			Command:     "vcli k8s create secret docker-registry regcred --docker-server=registry.io --docker-username=user --docker-password=pass",
		},
		{
			Description: "List all secrets",
			Command:     "vcli k8s get secrets",
		},
	},
}

// K8sWatchExamples provides examples for watch command
var K8sWatchExamples = ExampleGroup{
	Title: "Watch Resources",
	Examples: []Example{
		{
			Description: "Watch pods in real-time",
			Command:     "vcli k8s watch pods",
		},
		{
			Description: "Watch deployments",
			Command:     "vcli k8s watch deployments",
		},
		{
			Description: "Watch pods in specific namespace",
			Command:     "vcli k8s watch pods --namespace production",
		},
	},
}

// K8sWaitExamples provides examples for wait command
var K8sWaitExamples = ExampleGroup{
	Title: "Wait for Conditions",
	Examples: []Example{
		{
			Description: "Wait for pod to be ready",
			Command:     "vcli k8s wait pod nginx-pod --for=condition=Ready --timeout=60s",
		},
		{
			Description: "Wait for deployment to be available",
			Command:     "vcli k8s wait deployment nginx --for=condition=Available --timeout=5m",
		},
		{
			Description: "Wait for pod deletion",
			Command:     "vcli k8s wait pod nginx-pod --for=delete --timeout=30s",
		},
	},
}

// AllK8sExamples returns all Kubernetes example groups
func AllK8sExamples() []ExampleGroup {
	return []ExampleGroup{
		K8sGetExamples,
		K8sGetNodesExamples,
		K8sLogsExamples,
		K8sApplyExamples,
		K8sDeleteExamples,
		K8sScaleExamples,
		K8sExecExamples,
		K8sPortForwardExamples,
		K8sDescribeExamples,
		K8sRolloutExamples,
		K8sTopExamples,
		K8sLabelExamples,
		K8sAnnotateExamples,
		K8sAuthExamples,
		K8sConfigMapExamples,
		K8sSecretExamples,
		K8sWatchExamples,
		K8sWaitExamples,
	}
}

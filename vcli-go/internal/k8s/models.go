package k8s

import (
	"time"

	corev1 "k8s.io/api/core/v1"
	appsv1 "k8s.io/api/apps/v1"
)

// Pod represents a Kubernetes Pod
type Pod struct {
	Name              string
	Namespace         string
	Status            string
	Phase             corev1.PodPhase
	NodeName          string
	PodIP             string
	HostIP            string
	ContainerStatuses []ContainerStatus
	CreatedAt         time.Time
	Labels            map[string]string
	Annotations       map[string]string
}

// ContainerStatus represents the status of a container in a pod
type ContainerStatus struct {
	Name         string
	Image        string
	Ready        bool
	RestartCount int32
	State        string
}

// Namespace represents a Kubernetes Namespace
type Namespace struct {
	Name        string
	Status      string
	CreatedAt   time.Time
	Labels      map[string]string
	Annotations map[string]string
}

// Node represents a Kubernetes Node
type Node struct {
	Name        string
	Status      string
	Roles       []string
	Version     string
	OSImage     string
	KernelVersion string
	ContainerRuntime string
	Capacity    ResourceList
	Allocatable ResourceList
	Conditions  []NodeCondition
	CreatedAt   time.Time
	Labels      map[string]string
	Annotations map[string]string
}

// ResourceList represents compute resources
type ResourceList struct {
	CPU    string
	Memory string
	Pods   string
}

// NodeCondition represents a node condition
type NodeCondition struct {
	Type    string
	Status  string
	Reason  string
	Message string
}

// Deployment represents a Kubernetes Deployment
type Deployment struct {
	Name             string
	Namespace        string
	Replicas         int32
	ReadyReplicas    int32
	UpdatedReplicas  int32
	AvailableReplicas int32
	Strategy         string
	Selector         map[string]string
	CreatedAt        time.Time
	Labels           map[string]string
	Annotations      map[string]string
}

// Service represents a Kubernetes Service
type Service struct {
	Name        string
	Namespace   string
	Type        corev1.ServiceType
	ClusterIP   string
	ExternalIPs []string
	Ports       []ServicePort
	Selector    map[string]string
	CreatedAt   time.Time
	Labels      map[string]string
	Annotations map[string]string
}

// ServicePort represents a service port
type ServicePort struct {
	Name       string
	Protocol   corev1.Protocol
	Port       int32
	TargetPort string
	NodePort   int32
}

// convertPod converts a Kubernetes Pod to our internal model
func convertPod(k8sPod *corev1.Pod) Pod {
	pod := Pod{
		Name:        k8sPod.Name,
		Namespace:   k8sPod.Namespace,
		Status:      string(k8sPod.Status.Phase),
		Phase:       k8sPod.Status.Phase,
		NodeName:    k8sPod.Spec.NodeName,
		PodIP:       k8sPod.Status.PodIP,
		HostIP:      k8sPod.Status.HostIP,
		CreatedAt:   k8sPod.CreationTimestamp.Time,
		Labels:      k8sPod.Labels,
		Annotations: k8sPod.Annotations,
	}

	// Convert container statuses
	pod.ContainerStatuses = make([]ContainerStatus, len(k8sPod.Status.ContainerStatuses))
	for i, cs := range k8sPod.Status.ContainerStatuses {
		state := "Unknown"
		if cs.State.Running != nil {
			state = "Running"
		} else if cs.State.Waiting != nil {
			state = "Waiting"
		} else if cs.State.Terminated != nil {
			state = "Terminated"
		}

		pod.ContainerStatuses[i] = ContainerStatus{
			Name:         cs.Name,
			Image:        cs.Image,
			Ready:        cs.Ready,
			RestartCount: cs.RestartCount,
			State:        state,
		}
	}

	return pod
}

// convertNamespace converts a Kubernetes Namespace to our internal model
func convertNamespace(k8sNS *corev1.Namespace) Namespace {
	return Namespace{
		Name:        k8sNS.Name,
		Status:      string(k8sNS.Status.Phase),
		CreatedAt:   k8sNS.CreationTimestamp.Time,
		Labels:      k8sNS.Labels,
		Annotations: k8sNS.Annotations,
	}
}

// convertNode converts a Kubernetes Node to our internal model
func convertNode(k8sNode *corev1.Node) Node {
	node := Node{
		Name:      k8sNode.Name,
		CreatedAt: k8sNode.CreationTimestamp.Time,
		Labels:    k8sNode.Labels,
		Annotations: k8sNode.Annotations,
	}

	// Extract node info
	info := k8sNode.Status.NodeInfo
	node.Version = info.KubeletVersion
	node.OSImage = info.OSImage
	node.KernelVersion = info.KernelVersion
	node.ContainerRuntime = info.ContainerRuntimeVersion

	// Extract capacity and allocatable
	node.Capacity = ResourceList{
		CPU:    k8sNode.Status.Capacity.Cpu().String(),
		Memory: k8sNode.Status.Capacity.Memory().String(),
		Pods:   k8sNode.Status.Capacity.Pods().String(),
	}
	node.Allocatable = ResourceList{
		CPU:    k8sNode.Status.Allocatable.Cpu().String(),
		Memory: k8sNode.Status.Allocatable.Memory().String(),
		Pods:   k8sNode.Status.Allocatable.Pods().String(),
	}

	// Extract conditions
	node.Conditions = make([]NodeCondition, len(k8sNode.Status.Conditions))
	for i, cond := range k8sNode.Status.Conditions {
		node.Conditions[i] = NodeCondition{
			Type:    string(cond.Type),
			Status:  string(cond.Status),
			Reason:  cond.Reason,
			Message: cond.Message,
		}

		// Set overall node status from Ready condition
		if cond.Type == corev1.NodeReady {
			if cond.Status == corev1.ConditionTrue {
				node.Status = "Ready"
			} else {
				node.Status = "NotReady"
			}
		}
	}

	// Extract roles from labels
	roles := make([]string, 0)
	for label := range k8sNode.Labels {
		if label == "node-role.kubernetes.io/control-plane" ||
			label == "node-role.kubernetes.io/master" {
			roles = append(roles, "control-plane")
		}
		if label == "node-role.kubernetes.io/worker" {
			roles = append(roles, "worker")
		}
	}
	if len(roles) == 0 {
		roles = append(roles, "worker") // Default to worker if no role label
	}
	node.Roles = roles

	return node
}

// convertDeployment converts a Kubernetes Deployment to our internal model
func convertDeployment(k8sDeploy *appsv1.Deployment) Deployment {
	replicas := int32(0)
	if k8sDeploy.Spec.Replicas != nil {
		replicas = *k8sDeploy.Spec.Replicas
	}

	return Deployment{
		Name:              k8sDeploy.Name,
		Namespace:         k8sDeploy.Namespace,
		Replicas:          replicas,
		ReadyReplicas:     k8sDeploy.Status.ReadyReplicas,
		UpdatedReplicas:   k8sDeploy.Status.UpdatedReplicas,
		AvailableReplicas: k8sDeploy.Status.AvailableReplicas,
		Strategy:          string(k8sDeploy.Spec.Strategy.Type),
		Selector:          k8sDeploy.Spec.Selector.MatchLabels,
		CreatedAt:         k8sDeploy.CreationTimestamp.Time,
		Labels:            k8sDeploy.Labels,
		Annotations:       k8sDeploy.Annotations,
	}
}

// convertService converts a Kubernetes Service to our internal model
func convertService(k8sService *corev1.Service) Service {
	service := Service{
		Name:        k8sService.Name,
		Namespace:   k8sService.Namespace,
		Type:        k8sService.Spec.Type,
		ClusterIP:   k8sService.Spec.ClusterIP,
		Selector:    k8sService.Spec.Selector,
		CreatedAt:   k8sService.CreationTimestamp.Time,
		Labels:      k8sService.Labels,
		Annotations: k8sService.Annotations,
	}

	// Extract external IPs
	if len(k8sService.Spec.ExternalIPs) > 0 {
		service.ExternalIPs = k8sService.Spec.ExternalIPs
	}

	// Convert ports
	service.Ports = make([]ServicePort, len(k8sService.Spec.Ports))
	for i, port := range k8sService.Spec.Ports {
		service.Ports[i] = ServicePort{
			Name:       port.Name,
			Protocol:   port.Protocol,
			Port:       port.Port,
			TargetPort: port.TargetPort.String(),
			NodePort:   port.NodePort,
		}
	}

	return service
}

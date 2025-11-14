package k8s

import (
	"testing"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/intstr"
)

// TestConvertPod tests the convertPod function
func TestConvertPod(t *testing.T) {
	now := metav1.Now()
	k8sPod := &corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{
			Name:              "test-pod",
			Namespace:         "default",
			CreationTimestamp: now,
			Labels: map[string]string{
				"app": "test",
				"env": "prod",
			},
			Annotations: map[string]string{
				"description": "test pod",
			},
		},
		Spec: corev1.PodSpec{
			NodeName: "node-1",
		},
		Status: corev1.PodStatus{
			Phase:  corev1.PodRunning,
			PodIP:  "10.0.0.1",
			HostIP: "192.168.1.1",
			ContainerStatuses: []corev1.ContainerStatus{
				{
					Name:         "nginx",
					Image:        "nginx:1.21",
					Ready:        true,
					RestartCount: 0,
					State: corev1.ContainerState{
						Running: &corev1.ContainerStateRunning{
							StartedAt: now,
						},
					},
				},
				{
					Name:         "sidecar",
					Image:        "busybox:latest",
					Ready:        false,
					RestartCount: 2,
					State: corev1.ContainerState{
						Waiting: &corev1.ContainerStateWaiting{
							Reason: "CrashLoopBackOff",
						},
					},
				},
			},
		},
	}

	pod := convertPod(k8sPod)

	if pod.Name != "test-pod" {
		t.Errorf("Name = %q, want 'test-pod'", pod.Name)
	}
	if pod.Namespace != "default" {
		t.Errorf("Namespace = %q, want 'default'", pod.Namespace)
	}
	if pod.Status != "Running" {
		t.Errorf("Status = %q, want 'Running'", pod.Status)
	}
	if pod.Phase != corev1.PodRunning {
		t.Errorf("Phase = %v, want %v", pod.Phase, corev1.PodRunning)
	}
	if pod.NodeName != "node-1" {
		t.Errorf("NodeName = %q, want 'node-1'", pod.NodeName)
	}
	if pod.PodIP != "10.0.0.1" {
		t.Errorf("PodIP = %q, want '10.0.0.1'", pod.PodIP)
	}
	if pod.HostIP != "192.168.1.1" {
		t.Errorf("HostIP = %q, want '192.168.1.1'", pod.HostIP)
	}
	if !pod.CreatedAt.Equal(now.Time) {
		t.Errorf("CreatedAt mismatch")
	}
	if len(pod.Labels) != 2 {
		t.Errorf("Labels length = %d, want 2", len(pod.Labels))
	}
	if pod.Labels["app"] != "test" {
		t.Errorf("Labels[app] = %q, want 'test'", pod.Labels["app"])
	}
	if len(pod.Annotations) != 1 {
		t.Errorf("Annotations length = %d, want 1", len(pod.Annotations))
	}

	// Check container statuses
	if len(pod.ContainerStatuses) != 2 {
		t.Fatalf("ContainerStatuses length = %d, want 2", len(pod.ContainerStatuses))
	}

	// First container (running)
	cs1 := pod.ContainerStatuses[0]
	if cs1.Name != "nginx" {
		t.Errorf("Container[0].Name = %q, want 'nginx'", cs1.Name)
	}
	if cs1.Image != "nginx:1.21" {
		t.Errorf("Container[0].Image = %q, want 'nginx:1.21'", cs1.Image)
	}
	if !cs1.Ready {
		t.Error("Container[0].Ready should be true")
	}
	if cs1.RestartCount != 0 {
		t.Errorf("Container[0].RestartCount = %d, want 0", cs1.RestartCount)
	}
	if cs1.State != "Running" {
		t.Errorf("Container[0].State = %q, want 'Running'", cs1.State)
	}

	// Second container (waiting)
	cs2 := pod.ContainerStatuses[1]
	if cs2.Name != "sidecar" {
		t.Errorf("Container[1].Name = %q, want 'sidecar'", cs2.Name)
	}
	if cs2.Ready {
		t.Error("Container[1].Ready should be false")
	}
	if cs2.RestartCount != 2 {
		t.Errorf("Container[1].RestartCount = %d, want 2", cs2.RestartCount)
	}
	if cs2.State != "Waiting" {
		t.Errorf("Container[1].State = %q, want 'Waiting'", cs2.State)
	}
}

// TestConvertPod_TerminatedContainer tests terminated container state
func TestConvertPod_TerminatedContainer(t *testing.T) {
	k8sPod := &corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "terminated-pod",
			Namespace: "default",
		},
		Status: corev1.PodStatus{
			Phase: corev1.PodFailed,
			ContainerStatuses: []corev1.ContainerStatus{
				{
					Name:  "failed-container",
					Image: "app:latest",
					State: corev1.ContainerState{
						Terminated: &corev1.ContainerStateTerminated{
							ExitCode: 1,
							Reason:   "Error",
						},
					},
				},
			},
		},
	}

	pod := convertPod(k8sPod)

	if len(pod.ContainerStatuses) != 1 {
		t.Fatalf("ContainerStatuses length = %d, want 1", len(pod.ContainerStatuses))
	}
	if pod.ContainerStatuses[0].State != "Terminated" {
		t.Errorf("Container state = %q, want 'Terminated'", pod.ContainerStatuses[0].State)
	}
}

// TestConvertPod_UnknownState tests unknown container state
func TestConvertPod_UnknownState(t *testing.T) {
	k8sPod := &corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "unknown-pod",
			Namespace: "default",
		},
		Status: corev1.PodStatus{
			Phase: corev1.PodPending,
			ContainerStatuses: []corev1.ContainerStatus{
				{
					Name:  "pending-container",
					Image: "app:latest",
					State: corev1.ContainerState{
						// All state fields nil
					},
				},
			},
		},
	}

	pod := convertPod(k8sPod)

	if pod.ContainerStatuses[0].State != "Unknown" {
		t.Errorf("Container state = %q, want 'Unknown'", pod.ContainerStatuses[0].State)
	}
}

// TestConvertNamespace tests the convertNamespace function
func TestConvertNamespace(t *testing.T) {
	now := metav1.Now()
	k8sNS := &corev1.Namespace{
		ObjectMeta: metav1.ObjectMeta{
			Name:              "production",
			CreationTimestamp: now,
			Labels: map[string]string{
				"env": "prod",
			},
			Annotations: map[string]string{
				"owner": "platform-team",
			},
		},
		Status: corev1.NamespaceStatus{
			Phase: corev1.NamespaceActive,
		},
	}

	ns := convertNamespace(k8sNS)

	if ns.Name != "production" {
		t.Errorf("Name = %q, want 'production'", ns.Name)
	}
	if ns.Status != "Active" {
		t.Errorf("Status = %q, want 'Active'", ns.Status)
	}
	if !ns.CreatedAt.Equal(now.Time) {
		t.Errorf("CreatedAt mismatch")
	}
	if len(ns.Labels) != 1 {
		t.Errorf("Labels length = %d, want 1", len(ns.Labels))
	}
	if ns.Labels["env"] != "prod" {
		t.Errorf("Labels[env] = %q, want 'prod'", ns.Labels["env"])
	}
	if len(ns.Annotations) != 1 {
		t.Errorf("Annotations length = %d, want 1", len(ns.Annotations))
	}
	if ns.Annotations["owner"] != "platform-team" {
		t.Errorf("Annotations[owner] = %q", ns.Annotations["owner"])
	}
}

// TestConvertNode tests the convertNode function
func TestConvertNode(t *testing.T) {
	now := metav1.Now()
	k8sNode := &corev1.Node{
		ObjectMeta: metav1.ObjectMeta{
			Name:              "worker-1",
			CreationTimestamp: now,
			Labels: map[string]string{
				"node-role.kubernetes.io/worker": "",
				"topology.kubernetes.io/zone":    "us-west-1a",
			},
			Annotations: map[string]string{
				"node.alpha.kubernetes.io/ttl": "0",
			},
		},
		Status: corev1.NodeStatus{
			NodeInfo: corev1.NodeSystemInfo{
				KubeletVersion:          "v1.28.0",
				OSImage:                 "Ubuntu 22.04.3 LTS",
				KernelVersion:           "5.15.0-83-generic",
				ContainerRuntimeVersion: "containerd://1.7.2",
			},
			Capacity: corev1.ResourceList{
				corev1.ResourceCPU:    resource.MustParse("8"),
				corev1.ResourceMemory: resource.MustParse("16Gi"),
				corev1.ResourcePods:   resource.MustParse("110"),
			},
			Allocatable: corev1.ResourceList{
				corev1.ResourceCPU:    resource.MustParse("7800m"),
				corev1.ResourceMemory: resource.MustParse("15Gi"),
				corev1.ResourcePods:   resource.MustParse("100"),
			},
			Conditions: []corev1.NodeCondition{
				{
					Type:    corev1.NodeReady,
					Status:  corev1.ConditionTrue,
					Reason:  "KubeletReady",
					Message: "kubelet is posting ready status",
				},
				{
					Type:    corev1.NodeMemoryPressure,
					Status:  corev1.ConditionFalse,
					Reason:  "KubeletHasSufficientMemory",
					Message: "kubelet has sufficient memory available",
				},
			},
		},
	}

	node := convertNode(k8sNode)

	if node.Name != "worker-1" {
		t.Errorf("Name = %q, want 'worker-1'", node.Name)
	}
	if node.Status != "Ready" {
		t.Errorf("Status = %q, want 'Ready'", node.Status)
	}
	if node.Version != "v1.28.0" {
		t.Errorf("Version = %q, want 'v1.28.0'", node.Version)
	}
	if node.OSImage != "Ubuntu 22.04.3 LTS" {
		t.Errorf("OSImage = %q", node.OSImage)
	}
	if node.KernelVersion != "5.15.0-83-generic" {
		t.Errorf("KernelVersion = %q", node.KernelVersion)
	}
	if node.ContainerRuntime != "containerd://1.7.2" {
		t.Errorf("ContainerRuntime = %q", node.ContainerRuntime)
	}

	// Check capacity
	if node.Capacity.CPU != "8" {
		t.Errorf("Capacity.CPU = %q, want '8'", node.Capacity.CPU)
	}
	if node.Capacity.Memory != "16Gi" {
		t.Errorf("Capacity.Memory = %q, want '16Gi'", node.Capacity.Memory)
	}
	if node.Capacity.Pods != "110" {
		t.Errorf("Capacity.Pods = %q, want '110'", node.Capacity.Pods)
	}

	// Check allocatable
	if node.Allocatable.CPU != "7800m" {
		t.Errorf("Allocatable.CPU = %q, want '7800m'", node.Allocatable.CPU)
	}
	if node.Allocatable.Memory != "15Gi" {
		t.Errorf("Allocatable.Memory = %q, want '15Gi'", node.Allocatable.Memory)
	}
	if node.Allocatable.Pods != "100" {
		t.Errorf("Allocatable.Pods = %q, want '100'", node.Allocatable.Pods)
	}

	// Check conditions
	if len(node.Conditions) != 2 {
		t.Fatalf("Conditions length = %d, want 2", len(node.Conditions))
	}
	if node.Conditions[0].Type != "Ready" {
		t.Errorf("Condition[0].Type = %q, want 'Ready'", node.Conditions[0].Type)
	}
	if node.Conditions[0].Status != "True" {
		t.Errorf("Condition[0].Status = %q, want 'True'", node.Conditions[0].Status)
	}
	if node.Conditions[0].Reason != "KubeletReady" {
		t.Errorf("Condition[0].Reason = %q", node.Conditions[0].Reason)
	}

	// Check roles
	if len(node.Roles) != 1 {
		t.Fatalf("Roles length = %d, want 1", len(node.Roles))
	}
	if node.Roles[0] != "worker" {
		t.Errorf("Roles[0] = %q, want 'worker'", node.Roles[0])
	}

	if !node.CreatedAt.Equal(now.Time) {
		t.Errorf("CreatedAt mismatch")
	}
}

// TestConvertNode_ControlPlane tests control-plane node conversion
func TestConvertNode_ControlPlane(t *testing.T) {
	k8sNode := &corev1.Node{
		ObjectMeta: metav1.ObjectMeta{
			Name: "master-1",
			Labels: map[string]string{
				"node-role.kubernetes.io/control-plane": "",
			},
		},
		Status: corev1.NodeStatus{
			NodeInfo: corev1.NodeSystemInfo{
				KubeletVersion:          "v1.28.0",
				OSImage:                 "Ubuntu 22.04.3 LTS",
				KernelVersion:           "5.15.0-83-generic",
				ContainerRuntimeVersion: "containerd://1.7.2",
			},
			Capacity: corev1.ResourceList{
				corev1.ResourceCPU:    resource.MustParse("4"),
				corev1.ResourceMemory: resource.MustParse("8Gi"),
				corev1.ResourcePods:   resource.MustParse("110"),
			},
			Allocatable: corev1.ResourceList{
				corev1.ResourceCPU:    resource.MustParse("3800m"),
				corev1.ResourceMemory: resource.MustParse("7Gi"),
				corev1.ResourcePods:   resource.MustParse("100"),
			},
			Conditions: []corev1.NodeCondition{
				{
					Type:   corev1.NodeReady,
					Status: corev1.ConditionTrue,
				},
			},
		},
	}

	node := convertNode(k8sNode)

	if len(node.Roles) != 1 {
		t.Fatalf("Roles length = %d, want 1", len(node.Roles))
	}
	if node.Roles[0] != "control-plane" {
		t.Errorf("Roles[0] = %q, want 'control-plane'", node.Roles[0])
	}
}

// TestConvertNode_NotReady tests not ready node
func TestConvertNode_NotReady(t *testing.T) {
	k8sNode := &corev1.Node{
		ObjectMeta: metav1.ObjectMeta{
			Name: "worker-2",
		},
		Status: corev1.NodeStatus{
			NodeInfo: corev1.NodeSystemInfo{
				KubeletVersion:          "v1.28.0",
				OSImage:                 "Ubuntu 22.04.3 LTS",
				KernelVersion:           "5.15.0-83-generic",
				ContainerRuntimeVersion: "containerd://1.7.2",
			},
			Capacity: corev1.ResourceList{
				corev1.ResourceCPU:    resource.MustParse("4"),
				corev1.ResourceMemory: resource.MustParse("8Gi"),
				corev1.ResourcePods:   resource.MustParse("110"),
			},
			Allocatable: corev1.ResourceList{
				corev1.ResourceCPU:    resource.MustParse("3800m"),
				corev1.ResourceMemory: resource.MustParse("7Gi"),
				corev1.ResourcePods:   resource.MustParse("100"),
			},
			Conditions: []corev1.NodeCondition{
				{
					Type:   corev1.NodeReady,
					Status: corev1.ConditionFalse,
					Reason: "KubeletNotReady",
				},
			},
		},
	}

	node := convertNode(k8sNode)

	if node.Status != "NotReady" {
		t.Errorf("Status = %q, want 'NotReady'", node.Status)
	}

	// Should default to worker role
	if len(node.Roles) != 1 || node.Roles[0] != "worker" {
		t.Errorf("Roles = %v, want ['worker']", node.Roles)
	}
}

// TestConvertDeployment tests the convertDeployment function
func TestConvertDeployment(t *testing.T) {
	now := metav1.Now()
	replicas := int32(3)
	k8sDeploy := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:              "nginx-deployment",
			Namespace:         "default",
			CreationTimestamp: now,
			Labels: map[string]string{
				"app": "nginx",
			},
			Annotations: map[string]string{
				"deployment.kubernetes.io/revision": "3",
			},
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: &replicas,
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{
					"app": "nginx",
				},
			},
			Strategy: appsv1.DeploymentStrategy{
				Type: appsv1.RollingUpdateDeploymentStrategyType,
			},
		},
		Status: appsv1.DeploymentStatus{
			ReadyReplicas:     3,
			UpdatedReplicas:   3,
			AvailableReplicas: 3,
		},
	}

	deploy := convertDeployment(k8sDeploy)

	if deploy.Name != "nginx-deployment" {
		t.Errorf("Name = %q, want 'nginx-deployment'", deploy.Name)
	}
	if deploy.Namespace != "default" {
		t.Errorf("Namespace = %q, want 'default'", deploy.Namespace)
	}
	if deploy.Replicas != 3 {
		t.Errorf("Replicas = %d, want 3", deploy.Replicas)
	}
	if deploy.ReadyReplicas != 3 {
		t.Errorf("ReadyReplicas = %d, want 3", deploy.ReadyReplicas)
	}
	if deploy.UpdatedReplicas != 3 {
		t.Errorf("UpdatedReplicas = %d, want 3", deploy.UpdatedReplicas)
	}
	if deploy.AvailableReplicas != 3 {
		t.Errorf("AvailableReplicas = %d, want 3", deploy.AvailableReplicas)
	}
	if deploy.Strategy != "RollingUpdate" {
		t.Errorf("Strategy = %q, want 'RollingUpdate'", deploy.Strategy)
	}
	if len(deploy.Selector) != 1 {
		t.Fatalf("Selector length = %d, want 1", len(deploy.Selector))
	}
	if deploy.Selector["app"] != "nginx" {
		t.Errorf("Selector[app] = %q, want 'nginx'", deploy.Selector["app"])
	}
	if !deploy.CreatedAt.Equal(now.Time) {
		t.Errorf("CreatedAt mismatch")
	}
	if len(deploy.Labels) != 1 {
		t.Errorf("Labels length = %d, want 1", len(deploy.Labels))
	}
	if len(deploy.Annotations) != 1 {
		t.Errorf("Annotations length = %d, want 1", len(deploy.Annotations))
	}
}

// TestConvertDeployment_NilReplicas tests deployment with nil replicas
func TestConvertDeployment_NilReplicas(t *testing.T) {
	k8sDeploy := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "test-deploy",
			Namespace: "default",
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: nil, // nil replicas
			Selector: &metav1.LabelSelector{
				MatchLabels: map[string]string{},
			},
			Strategy: appsv1.DeploymentStrategy{
				Type: appsv1.RecreateDeploymentStrategyType,
			},
		},
	}

	deploy := convertDeployment(k8sDeploy)

	if deploy.Replicas != 0 {
		t.Errorf("Replicas = %d, want 0 (default for nil)", deploy.Replicas)
	}
	if deploy.Strategy != "Recreate" {
		t.Errorf("Strategy = %q, want 'Recreate'", deploy.Strategy)
	}
}

// TestConvertService tests the convertService function
func TestConvertService(t *testing.T) {
	now := metav1.Now()
	k8sService := &corev1.Service{
		ObjectMeta: metav1.ObjectMeta{
			Name:              "nginx-service",
			Namespace:         "default",
			CreationTimestamp: now,
			Labels: map[string]string{
				"app": "nginx",
			},
			Annotations: map[string]string{
				"service.beta.kubernetes.io/aws-load-balancer-type": "nlb",
			},
		},
		Spec: corev1.ServiceSpec{
			Type:      corev1.ServiceTypeLoadBalancer,
			ClusterIP: "10.96.0.1",
			ExternalIPs: []string{
				"203.0.113.1",
				"203.0.113.2",
			},
			Selector: map[string]string{
				"app": "nginx",
			},
			Ports: []corev1.ServicePort{
				{
					Name:       "http",
					Protocol:   corev1.ProtocolTCP,
					Port:       80,
					TargetPort: intstr.FromInt(8080),
					NodePort:   30080,
				},
				{
					Name:       "https",
					Protocol:   corev1.ProtocolTCP,
					Port:       443,
					TargetPort: intstr.FromString("https"),
					NodePort:   30443,
				},
			},
		},
	}

	service := convertService(k8sService)

	if service.Name != "nginx-service" {
		t.Errorf("Name = %q, want 'nginx-service'", service.Name)
	}
	if service.Namespace != "default" {
		t.Errorf("Namespace = %q, want 'default'", service.Namespace)
	}
	if service.Type != corev1.ServiceTypeLoadBalancer {
		t.Errorf("Type = %v, want %v", service.Type, corev1.ServiceTypeLoadBalancer)
	}
	if service.ClusterIP != "10.96.0.1" {
		t.Errorf("ClusterIP = %q, want '10.96.0.1'", service.ClusterIP)
	}

	// Check external IPs
	if len(service.ExternalIPs) != 2 {
		t.Fatalf("ExternalIPs length = %d, want 2", len(service.ExternalIPs))
	}
	if service.ExternalIPs[0] != "203.0.113.1" {
		t.Errorf("ExternalIPs[0] = %q", service.ExternalIPs[0])
	}

	// Check selector
	if len(service.Selector) != 1 {
		t.Fatalf("Selector length = %d, want 1", len(service.Selector))
	}
	if service.Selector["app"] != "nginx" {
		t.Errorf("Selector[app] = %q, want 'nginx'", service.Selector["app"])
	}

	// Check ports
	if len(service.Ports) != 2 {
		t.Fatalf("Ports length = %d, want 2", len(service.Ports))
	}

	// First port
	port1 := service.Ports[0]
	if port1.Name != "http" {
		t.Errorf("Port[0].Name = %q, want 'http'", port1.Name)
	}
	if port1.Protocol != corev1.ProtocolTCP {
		t.Errorf("Port[0].Protocol = %v, want TCP", port1.Protocol)
	}
	if port1.Port != 80 {
		t.Errorf("Port[0].Port = %d, want 80", port1.Port)
	}
	if port1.TargetPort != "8080" {
		t.Errorf("Port[0].TargetPort = %q, want '8080'", port1.TargetPort)
	}
	if port1.NodePort != 30080 {
		t.Errorf("Port[0].NodePort = %d, want 30080", port1.NodePort)
	}

	// Second port
	port2 := service.Ports[1]
	if port2.Name != "https" {
		t.Errorf("Port[1].Name = %q, want 'https'", port2.Name)
	}
	if port2.TargetPort != "https" {
		t.Errorf("Port[1].TargetPort = %q, want 'https'", port2.TargetPort)
	}

	if !service.CreatedAt.Equal(now.Time) {
		t.Errorf("CreatedAt mismatch")
	}
	if len(service.Labels) != 1 {
		t.Errorf("Labels length = %d, want 1", len(service.Labels))
	}
	if len(service.Annotations) != 1 {
		t.Errorf("Annotations length = %d, want 1", len(service.Annotations))
	}
}

// TestConvertService_NoExternalIPs tests service without external IPs
func TestConvertService_NoExternalIPs(t *testing.T) {
	k8sService := &corev1.Service{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "internal-service",
			Namespace: "default",
		},
		Spec: corev1.ServiceSpec{
			Type:      corev1.ServiceTypeClusterIP,
			ClusterIP: "10.96.0.2",
			Ports:     []corev1.ServicePort{},
		},
	}

	service := convertService(k8sService)

	if service.Type != corev1.ServiceTypeClusterIP {
		t.Errorf("Type = %v, want ClusterIP", service.Type)
	}
	if len(service.ExternalIPs) != 0 {
		t.Errorf("ExternalIPs length = %d, want 0", len(service.ExternalIPs))
	}
	if len(service.Ports) != 0 {
		t.Errorf("Ports length = %d, want 0", len(service.Ports))
	}
}

// TestConvertConfigMap tests the convertConfigMap function
func TestConvertConfigMap(t *testing.T) {
	now := metav1.Now()
	k8sCM := &corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{
			Name:              "app-config",
			Namespace:         "default",
			CreationTimestamp: now,
			Labels: map[string]string{
				"app": "myapp",
			},
			Annotations: map[string]string{
				"description": "Application configuration",
			},
		},
		Data: map[string]string{
			"database.host": "postgres.default.svc.cluster.local",
			"database.port": "5432",
			"log.level":     "info",
		},
		BinaryData: map[string][]byte{
			"cert.pem": []byte("CERTIFICATE DATA"),
		},
	}

	cm := convertConfigMap(k8sCM)

	if cm.Name != "app-config" {
		t.Errorf("Name = %q, want 'app-config'", cm.Name)
	}
	if cm.Namespace != "default" {
		t.Errorf("Namespace = %q, want 'default'", cm.Namespace)
	}

	// Check data
	if len(cm.Data) != 3 {
		t.Fatalf("Data length = %d, want 3", len(cm.Data))
	}
	if cm.Data["database.host"] != "postgres.default.svc.cluster.local" {
		t.Errorf("Data[database.host] = %q", cm.Data["database.host"])
	}
	if cm.Data["database.port"] != "5432" {
		t.Errorf("Data[database.port] = %q", cm.Data["database.port"])
	}
	if cm.Data["log.level"] != "info" {
		t.Errorf("Data[log.level] = %q", cm.Data["log.level"])
	}

	// Check binary data
	if len(cm.BinaryData) != 1 {
		t.Fatalf("BinaryData length = %d, want 1", len(cm.BinaryData))
	}
	if string(cm.BinaryData["cert.pem"]) != "CERTIFICATE DATA" {
		t.Errorf("BinaryData[cert.pem] mismatch")
	}

	if !cm.CreatedAt.Equal(now.Time) {
		t.Errorf("CreatedAt mismatch")
	}
	if len(cm.Labels) != 1 {
		t.Errorf("Labels length = %d, want 1", len(cm.Labels))
	}
	if cm.Labels["app"] != "myapp" {
		t.Errorf("Labels[app] = %q, want 'myapp'", cm.Labels["app"])
	}
	if len(cm.Annotations) != 1 {
		t.Errorf("Annotations length = %d, want 1", len(cm.Annotations))
	}
}

// TestConvertConfigMap_Empty tests empty configmap
func TestConvertConfigMap_Empty(t *testing.T) {
	k8sCM := &corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "empty-config",
			Namespace: "default",
		},
	}

	cm := convertConfigMap(k8sCM)

	if cm.Name != "empty-config" {
		t.Errorf("Name = %q, want 'empty-config'", cm.Name)
	}
	if cm.Data != nil {
		t.Errorf("Data should be nil for empty configmap")
	}
	if cm.BinaryData != nil {
		t.Errorf("BinaryData should be nil for empty configmap")
	}
}

// TestConvertSecret tests the convertSecret function
func TestConvertSecret(t *testing.T) {
	now := metav1.Now()
	k8sSecret := &corev1.Secret{
		ObjectMeta: metav1.ObjectMeta{
			Name:              "db-credentials",
			Namespace:         "default",
			CreationTimestamp: now,
			Labels: map[string]string{
				"app": "database",
			},
			Annotations: map[string]string{
				"description": "Database credentials",
			},
		},
		Type: corev1.SecretTypeOpaque,
		Data: map[string][]byte{
			"username": []byte("admin"),
			"password": []byte("supersecret"),
			"host":     []byte("postgres.default.svc.cluster.local"),
		},
	}

	secret := convertSecret(k8sSecret)

	if secret.Name != "db-credentials" {
		t.Errorf("Name = %q, want 'db-credentials'", secret.Name)
	}
	if secret.Namespace != "default" {
		t.Errorf("Namespace = %q, want 'default'", secret.Namespace)
	}
	if secret.Type != corev1.SecretTypeOpaque {
		t.Errorf("Type = %v, want %v", secret.Type, corev1.SecretTypeOpaque)
	}

	// Check data
	if len(secret.Data) != 3 {
		t.Fatalf("Data length = %d, want 3", len(secret.Data))
	}
	if string(secret.Data["username"]) != "admin" {
		t.Errorf("Data[username] = %q, want 'admin'", string(secret.Data["username"]))
	}
	if string(secret.Data["password"]) != "supersecret" {
		t.Errorf("Data[password] = %q", string(secret.Data["password"]))
	}
	if string(secret.Data["host"]) != "postgres.default.svc.cluster.local" {
		t.Errorf("Data[host] = %q", string(secret.Data["host"]))
	}

	if !secret.CreatedAt.Equal(now.Time) {
		t.Errorf("CreatedAt mismatch")
	}
	if len(secret.Labels) != 1 {
		t.Errorf("Labels length = %d, want 1", len(secret.Labels))
	}
	if secret.Labels["app"] != "database" {
		t.Errorf("Labels[app] = %q, want 'database'", secret.Labels["app"])
	}
	if len(secret.Annotations) != 1 {
		t.Errorf("Annotations length = %d, want 1", len(secret.Annotations))
	}
}

// TestConvertSecret_TLSType tests TLS secret conversion
func TestConvertSecret_TLSType(t *testing.T) {
	k8sSecret := &corev1.Secret{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "tls-cert",
			Namespace: "default",
		},
		Type: corev1.SecretTypeTLS,
		Data: map[string][]byte{
			"tls.crt": []byte("CERTIFICATE DATA"),
			"tls.key": []byte("PRIVATE KEY DATA"),
		},
	}

	secret := convertSecret(k8sSecret)

	if secret.Type != corev1.SecretTypeTLS {
		t.Errorf("Type = %v, want %v", secret.Type, corev1.SecretTypeTLS)
	}
	if len(secret.Data) != 2 {
		t.Fatalf("Data length = %d, want 2", len(secret.Data))
	}
}

// TestConvertSecret_DockerConfigJson tests docker config secret
func TestConvertSecret_DockerConfigJson(t *testing.T) {
	k8sSecret := &corev1.Secret{
		ObjectMeta: metav1.ObjectMeta{
			Name:      "docker-registry",
			Namespace: "default",
		},
		Type: corev1.SecretTypeDockerConfigJson,
		Data: map[string][]byte{
			".dockerconfigjson": []byte(`{"auths":{"https://index.docker.io/v1/":{"auth":"base64string"}}}`),
		},
	}

	secret := convertSecret(k8sSecret)

	if secret.Type != corev1.SecretTypeDockerConfigJson {
		t.Errorf("Type = %v, want %v", secret.Type, corev1.SecretTypeDockerConfigJson)
	}
	if len(secret.Data) != 1 {
		t.Fatalf("Data length = %d, want 1", len(secret.Data))
	}
}

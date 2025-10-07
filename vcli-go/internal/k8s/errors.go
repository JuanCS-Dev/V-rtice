package k8s

import "errors"

// ClusterManager errors
var (
	ErrKubeconfigPathEmpty = errors.New("kubeconfig path is empty")
	ErrKubeconfigNil       = errors.New("kubeconfig is nil")
	ErrNotConnected        = errors.New("not connected to cluster")
	ErrClientsetNil        = errors.New("clientset is nil")
	ErrContextNotFound     = errors.New("context not found")
	ErrAlreadyConnected    = errors.New("already connected to cluster")
)

// Kubeconfig errors
var (
	ErrKubeconfigFileNotFound = errors.New("kubeconfig file not found")
	ErrKubeconfigInvalid      = errors.New("kubeconfig is invalid")
	ErrKubeconfigParseFailed  = errors.New("failed to parse kubeconfig")
	ErrClusterNotFound        = errors.New("cluster not found in kubeconfig")
	ErrUserNotFound           = errors.New("user not found in kubeconfig")
	ErrNoCurrentContext       = errors.New("no current context in kubeconfig")
	ErrMissingClusterInfo     = errors.New("missing cluster information")
	ErrMissingUserInfo        = errors.New("missing user information")
)

// Operation errors
var (
	ErrNamespaceEmpty       = errors.New("namespace is empty")
	ErrResourceNameEmpty    = errors.New("resource name is empty")
	ErrOperationFailed      = errors.New("operation failed")
	ErrResourceNotFound     = errors.New("resource not found")
	ErrInvalidResourceType  = errors.New("invalid resource type")
)

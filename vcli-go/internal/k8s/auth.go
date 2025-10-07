package k8s

import (
	"context"
	"fmt"

	authenticationv1 "k8s.io/api/authentication/v1"
	authv1 "k8s.io/api/authorization/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

// AuthCheckResult represents the result of an authorization check
type AuthCheckResult struct {
	Allowed         bool
	Reason          string
	EvaluationError string
}

// UserInfo represents information about the current user
type UserInfo struct {
	Username string
	UID      string
	Groups   []string
	Extra    map[string][]string
}

// CanI checks if the current user can perform a specific action
func (cm *ClusterManager) CanI(verb, resource, namespace string) (*AuthCheckResult, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if verb == "" {
		return nil, fmt.Errorf("verb cannot be empty")
	}

	if resource == "" {
		return nil, fmt.Errorf("resource cannot be empty")
	}

	// Create SelfSubjectAccessReview
	ssar := &authv1.SelfSubjectAccessReview{
		Spec: authv1.SelfSubjectAccessReviewSpec{
			ResourceAttributes: &authv1.ResourceAttributes{
				Verb:      verb,
				Resource:  resource,
				Namespace: namespace,
			},
		},
	}

	ctx := context.Background()
	result, err := cm.clientset.AuthorizationV1().SelfSubjectAccessReviews().Create(ctx, ssar, metav1.CreateOptions{})
	if err != nil {
		return nil, fmt.Errorf("%w: failed to check authorization: %v", ErrOperationFailed, err)
	}

	authResult := &AuthCheckResult{
		Allowed:         result.Status.Allowed,
		Reason:          result.Status.Reason,
		EvaluationError: result.Status.EvaluationError,
	}

	return authResult, nil
}

// CanIWithResourceName checks if the current user can perform a specific action on a named resource
func (cm *ClusterManager) CanIWithResourceName(verb, resource, resourceName, namespace string) (*AuthCheckResult, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if verb == "" {
		return nil, fmt.Errorf("verb cannot be empty")
	}

	if resource == "" {
		return nil, fmt.Errorf("resource cannot be empty")
	}

	// Create SelfSubjectAccessReview with resource name
	ssar := &authv1.SelfSubjectAccessReview{
		Spec: authv1.SelfSubjectAccessReviewSpec{
			ResourceAttributes: &authv1.ResourceAttributes{
				Verb:      verb,
				Resource:  resource,
				Name:      resourceName,
				Namespace: namespace,
			},
		},
	}

	ctx := context.Background()
	result, err := cm.clientset.AuthorizationV1().SelfSubjectAccessReviews().Create(ctx, ssar, metav1.CreateOptions{})
	if err != nil {
		return nil, fmt.Errorf("%w: failed to check authorization: %v", ErrOperationFailed, err)
	}

	authResult := &AuthCheckResult{
		Allowed:         result.Status.Allowed,
		Reason:          result.Status.Reason,
		EvaluationError: result.Status.EvaluationError,
	}

	return authResult, nil
}

// CanIWithSubresource checks if the current user can perform a specific action on a subresource
func (cm *ClusterManager) CanIWithSubresource(verb, resource, subresource, namespace string) (*AuthCheckResult, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if verb == "" {
		return nil, fmt.Errorf("verb cannot be empty")
	}

	if resource == "" {
		return nil, fmt.Errorf("resource cannot be empty")
	}

	// Create SelfSubjectAccessReview with subresource
	ssar := &authv1.SelfSubjectAccessReview{
		Spec: authv1.SelfSubjectAccessReviewSpec{
			ResourceAttributes: &authv1.ResourceAttributes{
				Verb:        verb,
				Resource:    resource,
				Subresource: subresource,
				Namespace:   namespace,
			},
		},
	}

	ctx := context.Background()
	result, err := cm.clientset.AuthorizationV1().SelfSubjectAccessReviews().Create(ctx, ssar, metav1.CreateOptions{})
	if err != nil {
		return nil, fmt.Errorf("%w: failed to check authorization: %v", ErrOperationFailed, err)
	}

	authResult := &AuthCheckResult{
		Allowed:         result.Status.Allowed,
		Reason:          result.Status.Reason,
		EvaluationError: result.Status.EvaluationError,
	}

	return authResult, nil
}

// CanINonResource checks if the current user can perform a specific action on a non-resource URL
func (cm *ClusterManager) CanINonResource(verb, nonResourceURL string) (*AuthCheckResult, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if verb == "" {
		return nil, fmt.Errorf("verb cannot be empty")
	}

	if nonResourceURL == "" {
		return nil, fmt.Errorf("non-resource URL cannot be empty")
	}

	// Create SelfSubjectAccessReview for non-resource URL
	ssar := &authv1.SelfSubjectAccessReview{
		Spec: authv1.SelfSubjectAccessReviewSpec{
			NonResourceAttributes: &authv1.NonResourceAttributes{
				Verb: verb,
				Path: nonResourceURL,
			},
		},
	}

	ctx := context.Background()
	result, err := cm.clientset.AuthorizationV1().SelfSubjectAccessReviews().Create(ctx, ssar, metav1.CreateOptions{})
	if err != nil {
		return nil, fmt.Errorf("%w: failed to check authorization: %v", ErrOperationFailed, err)
	}

	authResult := &AuthCheckResult{
		Allowed:         result.Status.Allowed,
		Reason:          result.Status.Reason,
		EvaluationError: result.Status.EvaluationError,
	}

	return authResult, nil
}

// WhoAmI returns information about the current user
func (cm *ClusterManager) WhoAmI() (*UserInfo, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	// Create SelfSubjectReview to get current user info
	ctx := context.Background()

	// Use SelfSubjectReview to get user info
	ssr := &authenticationv1.SelfSubjectReview{}

	result, err := cm.clientset.AuthenticationV1().SelfSubjectReviews().Create(ctx, ssr, metav1.CreateOptions{})
	if err != nil {
		return nil, fmt.Errorf("%w: failed to get user info: %v", ErrOperationFailed, err)
	}

	// Extract user info from the review status
	userInfo := &UserInfo{
		Username: result.Status.UserInfo.Username,
		UID:      result.Status.UserInfo.UID,
		Groups:   result.Status.UserInfo.Groups,
		Extra:    make(map[string][]string),
	}

	// Copy extra fields
	for k, v := range result.Status.UserInfo.Extra {
		userInfo.Extra[k] = v
	}

	return userInfo, nil
}

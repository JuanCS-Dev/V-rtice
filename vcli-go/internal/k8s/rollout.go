package k8s

import (
	"context"
	"fmt"
	"sort"
	"time"

	appsv1 "k8s.io/api/apps/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
)

// RolloutStatus gets the rollout status of a deployment, statefulset, or daemonset
func (cm *ClusterManager) RolloutStatus(kind, name, namespace string, watch bool) (*RolloutStatusResult, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if namespace == "" {
		namespace = "default"
	}

	ctx := context.Background()

	switch kind {
	case "deployment", "deploy", "deployments":
		return cm.getDeploymentRolloutStatus(ctx, name, namespace, watch)
	case "statefulset", "sts", "statefulsets":
		return cm.getStatefulSetRolloutStatus(ctx, name, namespace, watch)
	case "daemonset", "ds", "daemonsets":
		return cm.getDaemonSetRolloutStatus(ctx, name, namespace, watch)
	default:
		return nil, fmt.Errorf("rollout status is only supported for deployments, statefulsets, and daemonsets")
	}
}

// RolloutHistory gets the rollout history (revisions) of a deployment or statefulset
func (cm *ClusterManager) RolloutHistory(kind, name, namespace string, revision int64) (*RolloutHistoryResult, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if namespace == "" {
		namespace = "default"
	}

	ctx := context.Background()

	switch kind {
	case "deployment", "deploy", "deployments":
		return cm.getDeploymentHistory(ctx, name, namespace, revision)
	case "statefulset", "sts", "statefulsets":
		return cm.getStatefulSetHistory(ctx, name, namespace, revision)
	case "daemonset", "ds", "daemonsets":
		return cm.getDaemonSetHistory(ctx, name, namespace, revision)
	default:
		return nil, fmt.Errorf("rollout history is only supported for deployments, statefulsets, and daemonsets")
	}
}

// RolloutUndo rolls back to a previous revision
func (cm *ClusterManager) RolloutUndo(kind, name, namespace string, toRevision int64) (*RolloutUndoResult, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return nil, ErrNotConnected
	}

	if namespace == "" {
		namespace = "default"
	}

	ctx := context.Background()

	switch kind {
	case "deployment", "deploy", "deployments":
		return cm.undoDeployment(ctx, name, namespace, toRevision)
	case "statefulset", "sts", "statefulsets":
		return cm.undoStatefulSet(ctx, name, namespace, toRevision)
	case "daemonset", "ds", "daemonsets":
		return cm.undoDaemonSet(ctx, name, namespace, toRevision)
	default:
		return nil, fmt.Errorf("rollout undo is only supported for deployments, statefulsets, and daemonsets")
	}
}

// RolloutRestart restarts a deployment, statefulset, or daemonset
func (cm *ClusterManager) RolloutRestart(kind, name, namespace string) error {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return ErrNotConnected
	}

	if namespace == "" {
		namespace = "default"
	}

	ctx := context.Background()

	// Restart by adding a restart annotation with current timestamp
	now := time.Now().Format(time.RFC3339)
	patchData := fmt.Sprintf(`{"spec":{"template":{"metadata":{"annotations":{"kubectl.kubernetes.io/restartedAt":"%s"}}}}}`, now)

	switch kind {
	case "deployment", "deploy", "deployments":
		_, err := cm.clientset.AppsV1().Deployments(namespace).Patch(ctx, name, types.StrategicMergePatchType, []byte(patchData), metav1.PatchOptions{})
		if err != nil {
			return fmt.Errorf("failed to restart deployment: %w", err)
		}
		return nil

	case "statefulset", "sts", "statefulsets":
		_, err := cm.clientset.AppsV1().StatefulSets(namespace).Patch(ctx, name, types.StrategicMergePatchType, []byte(patchData), metav1.PatchOptions{})
		if err != nil {
			return fmt.Errorf("failed to restart statefulset: %w", err)
		}
		return nil

	case "daemonset", "ds", "daemonsets":
		_, err := cm.clientset.AppsV1().DaemonSets(namespace).Patch(ctx, name, types.StrategicMergePatchType, []byte(patchData), metav1.PatchOptions{})
		if err != nil {
			return fmt.Errorf("failed to restart daemonset: %w", err)
		}
		return nil

	default:
		return fmt.Errorf("rollout restart is only supported for deployments, statefulsets, and daemonsets")
	}
}

// RolloutPause pauses a deployment rollout
func (cm *ClusterManager) RolloutPause(kind, name, namespace string) error {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return ErrNotConnected
	}

	if namespace == "" {
		namespace = "default"
	}

	ctx := context.Background()

	switch kind {
	case "deployment", "deploy", "deployments":
		// Get deployment
		deployment, err := cm.clientset.AppsV1().Deployments(namespace).Get(ctx, name, metav1.GetOptions{})
		if err != nil {
			return fmt.Errorf("failed to get deployment: %w", err)
		}

		// Check if already paused
		if deployment.Spec.Paused {
			return fmt.Errorf("deployment is already paused")
		}

		// Pause deployment
		deployment.Spec.Paused = true
		_, err = cm.clientset.AppsV1().Deployments(namespace).Update(ctx, deployment, metav1.UpdateOptions{})
		if err != nil {
			return fmt.Errorf("failed to pause deployment: %w", err)
		}
		return nil

	default:
		return fmt.Errorf("rollout pause is only supported for deployments")
	}
}

// RolloutResume resumes a paused deployment rollout
func (cm *ClusterManager) RolloutResume(kind, name, namespace string) error {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	if !cm.connected {
		return ErrNotConnected
	}

	if namespace == "" {
		namespace = "default"
	}

	ctx := context.Background()

	switch kind {
	case "deployment", "deploy", "deployments":
		// Get deployment
		deployment, err := cm.clientset.AppsV1().Deployments(namespace).Get(ctx, name, metav1.GetOptions{})
		if err != nil {
			return fmt.Errorf("failed to get deployment: %w", err)
		}

		// Check if not paused
		if !deployment.Spec.Paused {
			return fmt.Errorf("deployment is not paused")
		}

		// Resume deployment
		deployment.Spec.Paused = false
		_, err = cm.clientset.AppsV1().Deployments(namespace).Update(ctx, deployment, metav1.UpdateOptions{})
		if err != nil {
			return fmt.Errorf("failed to resume deployment: %w", err)
		}
		return nil

	default:
		return fmt.Errorf("rollout resume is only supported for deployments")
	}
}

// getDeploymentRolloutStatus gets deployment rollout status
func (cm *ClusterManager) getDeploymentRolloutStatus(ctx context.Context, name, namespace string, watch bool) (*RolloutStatusResult, error) {
	deployment, err := cm.clientset.AppsV1().Deployments(namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to get deployment: %w", err)
	}

	result := &RolloutStatusResult{
		Kind:              "Deployment",
		Name:              name,
		Namespace:         namespace,
		Replicas:          *deployment.Spec.Replicas,
		UpdatedReplicas:   deployment.Status.UpdatedReplicas,
		ReadyReplicas:     deployment.Status.ReadyReplicas,
		AvailableReplicas: deployment.Status.AvailableReplicas,
		Conditions:        []string{},
	}

	// Parse conditions
	for _, cond := range deployment.Status.Conditions {
		result.Conditions = append(result.Conditions, fmt.Sprintf("%s: %s (%s)", cond.Type, cond.Status, cond.Reason))
	}

	// Determine if rollout is complete
	result.Complete = deployment.Status.UpdatedReplicas == *deployment.Spec.Replicas &&
		deployment.Status.Replicas == *deployment.Spec.Replicas &&
		deployment.Status.AvailableReplicas == *deployment.Spec.Replicas

	// Determine status message
	if deployment.Spec.Paused {
		result.Message = "deployment is paused"
	} else if result.Complete {
		result.Message = fmt.Sprintf("deployment %q successfully rolled out", name)
	} else {
		result.Message = fmt.Sprintf("Waiting for deployment %q rollout to finish: %d out of %d new replicas have been updated...",
			name, deployment.Status.UpdatedReplicas, *deployment.Spec.Replicas)
	}

	// Get current revision
	if rev, ok := deployment.Annotations["deployment.kubernetes.io/revision"]; ok {
		fmt.Sscanf(rev, "%d", &result.CurrentRevision)
	}

	return result, nil
}

// getStatefulSetRolloutStatus gets statefulset rollout status
func (cm *ClusterManager) getStatefulSetRolloutStatus(ctx context.Context, name, namespace string, watch bool) (*RolloutStatusResult, error) {
	sts, err := cm.clientset.AppsV1().StatefulSets(namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to get statefulset: %w", err)
	}

	result := &RolloutStatusResult{
		Kind:              "StatefulSet",
		Name:              name,
		Namespace:         namespace,
		Replicas:          *sts.Spec.Replicas,
		UpdatedReplicas:   sts.Status.UpdatedReplicas,
		ReadyReplicas:     sts.Status.ReadyReplicas,
		AvailableReplicas: sts.Status.CurrentReplicas,
		Conditions:        []string{},
	}

	// Parse conditions
	for _, cond := range sts.Status.Conditions {
		result.Conditions = append(result.Conditions, fmt.Sprintf("%s: %s (%s)", cond.Type, cond.Status, cond.Reason))
	}

	// Determine if rollout is complete
	result.Complete = sts.Status.UpdatedReplicas == *sts.Spec.Replicas &&
		sts.Status.CurrentReplicas == *sts.Spec.Replicas &&
		sts.Status.ReadyReplicas == *sts.Spec.Replicas

	// Determine status message
	if result.Complete {
		result.Message = fmt.Sprintf("statefulset %q successfully rolled out", name)
	} else {
		result.Message = fmt.Sprintf("Waiting for statefulset %q rollout to finish: %d out of %d new replicas have been updated...",
			name, sts.Status.UpdatedReplicas, *sts.Spec.Replicas)
	}

	// Get current revision from status
	if sts.Status.CurrentRevision != "" {
		result.CurrentRevision = 1
	}

	return result, nil
}

// getDaemonSetRolloutStatus gets daemonset rollout status
func (cm *ClusterManager) getDaemonSetRolloutStatus(ctx context.Context, name, namespace string, watch bool) (*RolloutStatusResult, error) {
	ds, err := cm.clientset.AppsV1().DaemonSets(namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to get daemonset: %w", err)
	}

	result := &RolloutStatusResult{
		Kind:              "DaemonSet",
		Name:              name,
		Namespace:         namespace,
		Replicas:          ds.Status.DesiredNumberScheduled,
		UpdatedReplicas:   ds.Status.UpdatedNumberScheduled,
		ReadyReplicas:     ds.Status.NumberReady,
		AvailableReplicas: ds.Status.NumberAvailable,
		Conditions:        []string{},
	}

	// Parse conditions
	for _, cond := range ds.Status.Conditions {
		result.Conditions = append(result.Conditions, fmt.Sprintf("%s: %s (%s)", cond.Type, cond.Status, cond.Reason))
	}

	// Determine if rollout is complete
	result.Complete = ds.Status.UpdatedNumberScheduled == ds.Status.DesiredNumberScheduled &&
		ds.Status.NumberAvailable == ds.Status.DesiredNumberScheduled

	// Determine status message
	if result.Complete {
		result.Message = fmt.Sprintf("daemonset %q successfully rolled out", name)
	} else {
		result.Message = fmt.Sprintf("Waiting for daemonset %q rollout to finish: %d out of %d new pods have been updated...",
			name, ds.Status.UpdatedNumberScheduled, ds.Status.DesiredNumberScheduled)
	}

	return result, nil
}

// getDeploymentHistory gets deployment revision history
func (cm *ClusterManager) getDeploymentHistory(ctx context.Context, name, namespace string, revision int64) (*RolloutHistoryResult, error) {
	deployment, err := cm.clientset.AppsV1().Deployments(namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to get deployment: %w", err)
	}

	// Get ReplicaSets for this deployment
	selector, err := metav1.LabelSelectorAsSelector(deployment.Spec.Selector)
	if err != nil {
		return nil, fmt.Errorf("failed to parse selector: %w", err)
	}

	replicaSets, err := cm.clientset.AppsV1().ReplicaSets(namespace).List(ctx, metav1.ListOptions{
		LabelSelector: selector.String(),
	})
	if err != nil {
		return nil, fmt.Errorf("failed to list replicasets: %w", err)
	}

	result := &RolloutHistoryResult{
		Kind:      "Deployment",
		Name:      name,
		Namespace: namespace,
		Revisions: []RevisionInfo{},
	}

	// Parse revisions from ReplicaSets
	for _, rs := range replicaSets.Items {
		if revStr, ok := rs.Annotations["deployment.kubernetes.io/revision"]; ok {
			var revNum int64
			fmt.Sscanf(revStr, "%d", &revNum)

			changeNote := rs.Annotations["kubernetes.io/change-cause"]
			if changeNote == "" {
				changeNote = "<none>"
			}

			revInfo := RevisionInfo{
				Revision:    revNum,
				ChangeCause: changeNote,
				CreatedAt:   rs.CreationTimestamp.Time,
			}

			result.Revisions = append(result.Revisions, revInfo)
		}
	}

	// Sort by revision number
	sort.Slice(result.Revisions, func(i, j int) bool {
		return result.Revisions[i].Revision < result.Revisions[j].Revision
	})

	// If specific revision requested, filter
	if revision > 0 {
		for i, rev := range result.Revisions {
			if rev.Revision == revision {
				result.Revisions = []RevisionInfo{result.Revisions[i]}
				break
			}
		}
	}

	return result, nil
}

// getStatefulSetHistory gets statefulset revision history
func (cm *ClusterManager) getStatefulSetHistory(ctx context.Context, name, namespace string, revision int64) (*RolloutHistoryResult, error) {
	sts, err := cm.clientset.AppsV1().StatefulSets(namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to get statefulset: %w", err)
	}

	// Get ControllerRevisions for this statefulset
	selector, err := metav1.LabelSelectorAsSelector(sts.Spec.Selector)
	if err != nil {
		return nil, fmt.Errorf("failed to parse selector: %w", err)
	}

	revisions, err := cm.clientset.AppsV1().ControllerRevisions(namespace).List(ctx, metav1.ListOptions{
		LabelSelector: selector.String(),
	})
	if err != nil {
		return nil, fmt.Errorf("failed to list controller revisions: %w", err)
	}

	result := &RolloutHistoryResult{
		Kind:      "StatefulSet",
		Name:      name,
		Namespace: namespace,
		Revisions: []RevisionInfo{},
	}

	// Parse revisions
	for _, rev := range revisions.Items {
		changeNote := rev.Annotations["kubernetes.io/change-cause"]
		if changeNote == "" {
			changeNote = "<none>"
		}

		revInfo := RevisionInfo{
			Revision:    rev.Revision,
			ChangeCause: changeNote,
			CreatedAt:   rev.CreationTimestamp.Time,
		}

		result.Revisions = append(result.Revisions, revInfo)
	}

	// Sort by revision number
	sort.Slice(result.Revisions, func(i, j int) bool {
		return result.Revisions[i].Revision < result.Revisions[j].Revision
	})

	// If specific revision requested, filter
	if revision > 0 {
		for i, rev := range result.Revisions {
			if rev.Revision == revision {
				result.Revisions = []RevisionInfo{result.Revisions[i]}
				break
			}
		}
	}

	return result, nil
}

// getDaemonSetHistory gets daemonset revision history
func (cm *ClusterManager) getDaemonSetHistory(ctx context.Context, name, namespace string, revision int64) (*RolloutHistoryResult, error) {
	ds, err := cm.clientset.AppsV1().DaemonSets(namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to get daemonset: %w", err)
	}

	// Get ControllerRevisions for this daemonset
	selector, err := metav1.LabelSelectorAsSelector(ds.Spec.Selector)
	if err != nil {
		return nil, fmt.Errorf("failed to parse selector: %w", err)
	}

	revisions, err := cm.clientset.AppsV1().ControllerRevisions(namespace).List(ctx, metav1.ListOptions{
		LabelSelector: selector.String(),
	})
	if err != nil {
		return nil, fmt.Errorf("failed to list controller revisions: %w", err)
	}

	result := &RolloutHistoryResult{
		Kind:      "DaemonSet",
		Name:      name,
		Namespace: namespace,
		Revisions: []RevisionInfo{},
	}

	// Parse revisions
	for _, rev := range revisions.Items {
		changeNote := rev.Annotations["kubernetes.io/change-cause"]
		if changeNote == "" {
			changeNote = "<none>"
		}

		revInfo := RevisionInfo{
			Revision:    rev.Revision,
			ChangeCause: changeNote,
			CreatedAt:   rev.CreationTimestamp.Time,
		}

		result.Revisions = append(result.Revisions, revInfo)
	}

	// Sort by revision number
	sort.Slice(result.Revisions, func(i, j int) bool {
		return result.Revisions[i].Revision < result.Revisions[j].Revision
	})

	// If specific revision requested, filter
	if revision > 0 {
		for i, rev := range result.Revisions {
			if rev.Revision == revision {
				result.Revisions = []RevisionInfo{result.Revisions[i]}
				break
			}
		}
	}

	return result, nil
}

// undoDeployment rolls back deployment to previous or specific revision
func (cm *ClusterManager) undoDeployment(ctx context.Context, name, namespace string, toRevision int64) (*RolloutUndoResult, error) {
	deployment, err := cm.clientset.AppsV1().Deployments(namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to get deployment: %w", err)
	}

	// Get current revision
	currentRev := int64(1)
	if revStr, ok := deployment.Annotations["deployment.kubernetes.io/revision"]; ok {
		fmt.Sscanf(revStr, "%d", &currentRev)
	}

	// If no specific revision specified, rollback to previous
	targetRevision := toRevision
	if targetRevision == 0 {
		targetRevision = currentRev - 1
	}

	// Perform rollback using rollback annotation
	patchData := fmt.Sprintf(`{"spec":{"rollbackTo":{"revision":%d}}}`, targetRevision)
	_, err = cm.clientset.AppsV1().Deployments(namespace).Patch(ctx, name, types.StrategicMergePatchType, []byte(patchData), metav1.PatchOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to rollback deployment: %w", err)
	}

	return &RolloutUndoResult{
		Kind:           "Deployment",
		Name:           name,
		Namespace:      namespace,
		FromRevision:   currentRev,
		ToRevision:     targetRevision,
		Success:        true,
		Message:        fmt.Sprintf("deployment %q rolled back to revision %d", name, targetRevision),
	}, nil
}

// undoStatefulSet rolls back statefulset to previous or specific revision
func (cm *ClusterManager) undoStatefulSet(ctx context.Context, name, namespace string, toRevision int64) (*RolloutUndoResult, error) {
	sts, err := cm.clientset.AppsV1().StatefulSets(namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to get statefulset: %w", err)
	}

	// Get target ControllerRevision
	if toRevision == 0 {
		return nil, fmt.Errorf("must specify a revision to rollback to for statefulsets")
	}

	// Get ControllerRevision
	selector, err := metav1.LabelSelectorAsSelector(sts.Spec.Selector)
	if err != nil {
		return nil, fmt.Errorf("failed to parse selector: %w", err)
	}

	revisions, err := cm.clientset.AppsV1().ControllerRevisions(namespace).List(ctx, metav1.ListOptions{
		LabelSelector: selector.String(),
	})
	if err != nil {
		return nil, fmt.Errorf("failed to list controller revisions: %w", err)
	}

	// Find target revision
	var targetRev *appsv1.ControllerRevision
	for _, rev := range revisions.Items {
		if rev.Revision == toRevision {
			targetRev = &rev
			break
		}
	}

	if targetRev == nil {
		return nil, fmt.Errorf("revision %d not found", toRevision)
	}

	// Update statefulset with revision template
	patchData := fmt.Sprintf(`{"spec":{"updateRevision":"%s"}}`, targetRev.Name)
	_, err = cm.clientset.AppsV1().StatefulSets(namespace).Patch(ctx, name, types.MergePatchType, []byte(patchData), metav1.PatchOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to rollback statefulset: %w", err)
	}

	return &RolloutUndoResult{
		Kind:           "StatefulSet",
		Name:           name,
		Namespace:      namespace,
		FromRevision:   0,
		ToRevision:     toRevision,
		Success:        true,
		Message:        fmt.Sprintf("statefulset %q rolled back to revision %d", name, toRevision),
	}, nil
}

// undoDaemonSet rolls back daemonset to previous or specific revision
func (cm *ClusterManager) undoDaemonSet(ctx context.Context, name, namespace string, toRevision int64) (*RolloutUndoResult, error) {
	ds, err := cm.clientset.AppsV1().DaemonSets(namespace).Get(ctx, name, metav1.GetOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to get daemonset: %w", err)
	}

	// Get target ControllerRevision
	if toRevision == 0 {
		return nil, fmt.Errorf("must specify a revision to rollback to for daemonsets")
	}

	// Get ControllerRevision
	selector, err := metav1.LabelSelectorAsSelector(ds.Spec.Selector)
	if err != nil {
		return nil, fmt.Errorf("failed to parse selector: %w", err)
	}

	revisions, err := cm.clientset.AppsV1().ControllerRevisions(namespace).List(ctx, metav1.ListOptions{
		LabelSelector: selector.String(),
	})
	if err != nil {
		return nil, fmt.Errorf("failed to list controller revisions: %w", err)
	}

	// Find target revision
	var targetRev *appsv1.ControllerRevision
	for _, rev := range revisions.Items {
		if rev.Revision == toRevision {
			targetRev = &rev
			break
		}
	}

	if targetRev == nil {
		return nil, fmt.Errorf("revision %d not found", toRevision)
	}

	// Update daemonset template annotation to trigger rollback
	patchData := fmt.Sprintf(`{"spec":{"template":{"metadata":{"annotations":{"rollback.kubernetes.io/revision":"%d"}}}}}`, toRevision)
	_, err = cm.clientset.AppsV1().DaemonSets(namespace).Patch(ctx, name, types.StrategicMergePatchType, []byte(patchData), metav1.PatchOptions{})
	if err != nil {
		return nil, fmt.Errorf("failed to rollback daemonset: %w", err)
	}

	return &RolloutUndoResult{
		Kind:           "DaemonSet",
		Name:           name,
		Namespace:      namespace,
		FromRevision:   0,
		ToRevision:     toRevision,
		Success:        true,
		Message:        fmt.Sprintf("daemonset %q rolled back to revision %d", name, toRevision),
	}, nil
}

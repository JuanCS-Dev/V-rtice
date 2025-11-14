package edge

type DeployRequest struct {
	Agent  string
	Target string
}

type DeployResult struct {
	Agent  string
	Target string
	Status string
}

type ListResult struct {
	Agents []AgentInfo
}

type AgentInfo struct {
	Name    string
	Target  string
	Status  string
	Version string
}

type StatusResult struct {
	Status       string
	ActiveAgents int
}

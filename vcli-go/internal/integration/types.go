package integration

type ListResult struct {
	Integrations []IntegrationInfo
}

type IntegrationInfo struct {
	Name   string
	Type   string
	Status string
	Health float64
}

type TestRequest struct {
	Integration string
}

type TestResult struct {
	Integration  string
	Status       string
	ResponseTime int
}

type StatusResult struct {
	Status             string
	ActiveIntegrations int
}

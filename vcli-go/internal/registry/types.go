package registry

type ListResult struct {
	Services []ServiceInfo
}

type ServiceInfo struct {
	Name     string
	Endpoint string
	Status   string
	Health   float64
}

type HealthRequest struct {
	Service string
}

type HealthResult struct {
	Service      string
	Status       string
	Health       float64
	ResponseTime int
}

type StatusResult struct {
	Status             string
	RegisteredServices int
	ActiveSidecars     int
}

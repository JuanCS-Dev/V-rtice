package homeostasis

type StatusResult struct {
	Status     string
	Balance    float64
	Parameters []Parameter
}

type Parameter struct {
	Name   string
	Value  float64
	Status string
}

type AdjustRequest struct {
	Parameter string
	Value     string
}

type AdjustResult struct {
	Parameter string
	Value     string
	Status    string
}

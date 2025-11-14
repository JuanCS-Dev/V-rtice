package immunity

// ============================================================================
// IMMUNE CORE
// ============================================================================

type CoreStatusRequest struct {
	Zone string
}

type CoreStatusResult struct {
	Zone             string
	Status           string
	Health           float64
	ActiveThreats    int
	DeployedVaccines int
	ActiveAntibodies int
	Subsystems       []Subsystem
}

type Subsystem struct {
	Name   string
	Status string
	Health float64
}

type CoreActivateRequest struct {
	Zone   string
	Policy string
}

type CoreActivateResult struct {
	ActivationID        string
	Zone                string
	Policy              string
	Status              string
	ActivatedSubsystems []string
}

// ============================================================================
// IMMUNIS SCANNER
// ============================================================================

type ImmunisScanRequest struct {
	Target string
	Mode   string
}

type ImmunisScanResult struct {
	Target          string
	ScanID          string
	Duration        float64
	ItemsScanned    int
	Vulnerabilities []Vulnerability
}

type Vulnerability struct {
	CVE           string
	SeverityScore int
	Component     string
	Status        string
	Description   string
}

// ============================================================================
// VACCINE MANAGEMENT
// ============================================================================

type VaccineDeployRequest struct {
	Vaccine string
	Zone    string
}

type VaccineDeployResult struct {
	Vaccine             string
	DeploymentID        string
	Zone                string
	Status              string
	HostsProtected      int
	ProtectedComponents []string
}

type VaccineListRequest struct {
	Zone string
}

type VaccineListResult struct {
	Vaccines []VaccineInfo
}

type VaccineInfo struct {
	Name             string
	Type             string
	Severity         string
	DeploymentStatus string
}

// ============================================================================
// ANTIBODY RESPONSE
// ============================================================================

type AntibodyGenerateRequest struct {
	Threat   string
	Severity string
}

type AntibodyGenerateResult struct {
	AntibodyID      string
	Threat          string
	Type            string
	Efficacy        float64
	Status          string
	Countermeasures []Countermeasure
}

type Countermeasure struct {
	Type        string
	Description string
}

type AntibodyListRequest struct {
	Zone string
}

type AntibodyListResult struct {
	Antibodies []AntibodyInfo
}

type AntibodyInfo struct {
	ID       string
	Threat   string
	Type     string
	Efficacy float64
	Status   string
}

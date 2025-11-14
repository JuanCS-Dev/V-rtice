package purple

type ExerciseRequest struct {
	Scenario string
}

type ExerciseResult struct {
	ExerciseID   string
	Scenario     string
	Status       string
	AttackSteps  []string
	DefenseSteps []string
}

type ReportRequest struct {
	ExerciseID string
}

type ReportResult struct {
	ExerciseID string
	Detected   int
	Total      int
	Coverage   float64
	Gaps       []string
}

type StatusResult struct {
	Status             string
	ExercisesCompleted int
}

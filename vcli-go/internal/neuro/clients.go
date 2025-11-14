package neuro

import (
	"context"
	"fmt"

	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/httpclient"
)

type NeuroClient struct {
	httpClient *httpclient.Client
	endpoint   string
}

func NewNeuroClient(endpoint string) *NeuroClient {
	if endpoint == "" {
		endpoint = config.GetEndpoint("neuro")
	}

	clientConfig := httpclient.DefaultClientConfig(endpoint)
	return &NeuroClient{
		httpClient: httpclient.NewClient(clientConfig),
		endpoint:   endpoint,
	}
}

func (c *NeuroClient) ListenAuditory(req *AuditoryListenRequest) ([]AuditoryEvent, error) {
	ctx := context.Background()

	var result []AuditoryEvent
	err := c.httpClient.PostJSONResponse(ctx, "/auditory/listen", req, &result)
	if err != nil {
		return nil, fmt.Errorf("listen auditory failed: %w", err)
	}

	return result, nil
}

func (c *NeuroClient) RouteThalamus(req *ThalamusRouteRequest) (*ThalamusRouteResult, error) {
	ctx := context.Background()

	var result ThalamusRouteResult
	err := c.httpClient.PostJSONResponse(ctx, "/thalamus/route", req, &result)
	if err != nil {
		return nil, fmt.Errorf("route thalamus failed: %w", err)
	}

	return &result, nil
}

func (c *NeuroClient) ConsolidateMemory(req *MemoryConsolidateRequest) (*MemoryConsolidateResult, error) {
	ctx := context.Background()

	var result MemoryConsolidateResult
	err := c.httpClient.PostJSONResponse(ctx, "/memory/consolidate", req, &result)
	if err != nil {
		return nil, fmt.Errorf("consolidate memory failed: %w", err)
	}

	return &result, nil
}

func (c *NeuroClient) PlanCortex(req *CortexPlanRequest) (*CortexPlan, error) {
	ctx := context.Background()

	var result CortexPlan
	err := c.httpClient.PostJSONResponse(ctx, "/cortex/plan", req, &result)
	if err != nil {
		return nil, fmt.Errorf("plan cortex failed: %w", err)
	}

	return &result, nil
}

func (c *NeuroClient) AnalyzeVisual(req *VisualAnalyzeRequest) (*VisualAnalyzeResult, error) {
	ctx := context.Background()

	var result VisualAnalyzeResult
	err := c.httpClient.PostJSONResponse(ctx, "/visual/analyze", req, &result)
	if err != nil {
		return nil, fmt.Errorf("analyze visual failed: %w", err)
	}

	return &result, nil
}

func (c *NeuroClient) GetSomatosensoryStatus() (*SomatosensoryStatus, error) {
	ctx := context.Background()

	var result SomatosensoryStatus
	err := c.httpClient.GetJSON(ctx, "/somatosensory/status", &result)
	if err != nil {
		return nil, fmt.Errorf("get somatosensory status failed: %w", err)
	}

	return &result, nil
}

func (c *NeuroClient) ActivateTegumentar(req *TegumentarShieldRequest) (*TegumentarShieldResult, error) {
	ctx := context.Background()

	var result TegumentarShieldResult
	err := c.httpClient.PostJSONResponse(ctx, "/tegumentar/shield", req, &result)
	if err != nil {
		return nil, fmt.Errorf("activate tegumentar failed: %w", err)
	}

	return &result, nil
}

func (c *NeuroClient) BalanceVestibular(req *VestibularBalanceRequest) (*VestibularBalanceResult, error) {
	ctx := context.Background()

	var result VestibularBalanceResult
	err := c.httpClient.PostJSONResponse(ctx, "/vestibular/balance", req, &result)
	if err != nil {
		return nil, fmt.Errorf("balance vestibular failed: %w", err)
	}

	return &result, nil
}

func (c *NeuroClient) SenseChemical(req *ChemicalSenseRequest) (*ChemicalSenseResult, error) {
	ctx := context.Background()

	var result ChemicalSenseResult
	err := c.httpClient.PostJSONResponse(ctx, "/chemical/sense", req, &result)
	if err != nil {
		return nil, fmt.Errorf("sense chemical failed: %w", err)
	}

	return &result, nil
}

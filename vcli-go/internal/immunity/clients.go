package immunity

import (
	"context"
	"fmt"

	"github.com/verticedev/vcli-go/internal/config"
	"github.com/verticedev/vcli-go/internal/httpclient"
)

type ImmunityClient struct {
	httpClient *httpclient.Client
	endpoint   string
}

func NewImmunityClient(endpoint string) *ImmunityClient {
	if endpoint == "" {
		endpoint = config.GetEndpoint("immunity")
	}

	clientConfig := httpclient.DefaultClientConfig(endpoint)
	return &ImmunityClient{
		httpClient: httpclient.NewClient(clientConfig),
		endpoint:   endpoint,
	}
}

func (c *ImmunityClient) GetStatus() (*CoreStatusResult, error) {
	ctx := context.Background()

	var result CoreStatusResult
	err := c.httpClient.GetJSON(ctx, "/core/status", &result)
	if err != nil {
		return nil, fmt.Errorf("get immune status failed: %w", err)
	}

	return &result, nil
}

func (c *ImmunityClient) ActivateResponse(req *CoreActivateRequest) (*CoreActivateResult, error) {
	ctx := context.Background()

	var result CoreActivateResult
	err := c.httpClient.PostJSONResponse(ctx, "/core/activate", req, &result)
	if err != nil {
		return nil, fmt.Errorf("activate response failed: %w", err)
	}

	return &result, nil
}

func (c *ImmunityClient) Scan(req *ImmunisScanRequest) (*ImmunisScanResult, error) {
	ctx := context.Background()

	var result ImmunisScanResult
	err := c.httpClient.PostJSONResponse(ctx, "/immunis/scan", req, &result)
	if err != nil {
		return nil, fmt.Errorf("immunis scan failed: %w", err)
	}

	return &result, nil
}

func (c *ImmunityClient) DeployVaccine(req *VaccineDeployRequest) (*VaccineDeployResult, error) {
	ctx := context.Background()

	var result VaccineDeployResult
	err := c.httpClient.PostJSONResponse(ctx, "/vaccine/deploy", req, &result)
	if err != nil {
		return nil, fmt.Errorf("deploy vaccine failed: %w", err)
	}

	return &result, nil
}

func (c *ImmunityClient) ListVaccines() (*VaccineListResult, error) {
	ctx := context.Background()

	var result VaccineListResult
	err := c.httpClient.GetJSON(ctx, "/vaccine/list", &result)
	if err != nil {
		return nil, fmt.Errorf("list vaccines failed: %w", err)
	}

	return &result, nil
}

func (c *ImmunityClient) GenerateAntibody(req *AntibodyGenerateRequest) (*AntibodyGenerateResult, error) {
	ctx := context.Background()

	var result AntibodyGenerateResult
	err := c.httpClient.PostJSONResponse(ctx, "/antibody/generate", req, &result)
	if err != nil {
		return nil, fmt.Errorf("generate antibody failed: %w", err)
	}

	return &result, nil
}

func (c *ImmunityClient) ListAntibodies() (*AntibodyListResult, error) {
	ctx := context.Background()

	var result AntibodyListResult
	err := c.httpClient.GetJSON(ctx, "/antibody/list", &result)
	if err != nil {
		return nil, fmt.Errorf("list antibodies failed: %w", err)
	}

	return &result, nil
}

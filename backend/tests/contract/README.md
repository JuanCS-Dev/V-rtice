# Contract Testing Guide

## 🎯 Purpose

Contract tests ensure the API contract between frontend and backend remains stable. These tests validate:
- OpenAPI schema validity
- Endpoint availability
- Response format consistency
- Backward compatibility
- Breaking change detection

## 🧪 Test Structure

### Backend Tests (`test_openapi_contract.py`)
- **Schema Validation**: OpenAPI schema is valid and accessible
- **Endpoint Documentation**: All routes are documented
- **Response Schema**: Responses match documented schemas
- **Backward Compatibility**: Core endpoints remain stable
- **Performance**: Schema generation is fast

### Frontend Tests (`frontend/tests/contract/openapi.test.ts`)
- **Schema Accessibility**: Can fetch OpenAPI schema
- **Required Endpoints**: Core endpoints exist
- **Response Format**: Responses match expected format
- **Headers**: Version and request ID headers present
- **Error Format**: Errors follow standard format

## 🚀 Running Contract Tests

### Locally

**Backend Only:**
```bash
# From backend directory
pytest tests/contract/ -v
```

**Frontend Only:**
```bash
# From frontend directory
npm run test:contract
```

**Full Contract Suite:**
```bash
# From project root
./backend/scripts/run_contract_tests.sh
```

### Requirements
- API Gateway must be running at `http://localhost:8000`
- All backend dependencies installed
- Frontend dependencies installed (`npm install`)

## 📋 Pre-requisites

**Backend:**
```bash
cd backend/api_gateway
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx

# Start API Gateway
python main.py
```

**Frontend:**
```bash
cd frontend
npm install
```

## 🔍 What Gets Tested

### 1. Schema Validation
- OpenAPI 3.x compliance
- Required fields present (openapi, info, paths)
- Security schemes documented (BearerAuth, ApiKeyAuth)

### 2. Endpoint Contracts
- `/api/v1/health` - Health check endpoint
- `/api/v1/` - API root endpoint
- All versioned endpoints under `/api/v1/*`

### 3. Response Formats
- Health response has `status`, `version`, `timestamp`, `services`
- Error responses have `detail`, `error_code`, `request_id`, `path`, `timestamp`
- Validation errors include field-level details

### 4. Headers
- `X-API-Version: v1` on all v1 endpoints
- `X-Request-ID` on all responses (UUID v4 format)
- Request ID propagation from client to server

### 5. Backward Compatibility
- Core v1 endpoints not removed
- Required response fields not removed
- Error format remains consistent

## 🛠️ CI/CD Integration

Contract tests run automatically in GitHub Actions:

```yaml
# .github/workflows/contract-tests.yml
- Backend contract tests
- Frontend contract tests
- Breaking change detection (PRs only)
```

### Breaking Change Detection

On pull requests, the CI compares OpenAPI schemas:
- Base branch schema vs PR branch schema
- Fails if breaking changes detected
- Comments on PR with warning

## 📊 Test Coverage

| Category | Backend Tests | Frontend Tests |
|----------|---------------|----------------|
| Schema Validation | ✅ | ✅ |
| Endpoint Contracts | ✅ | ✅ |
| Response Format | ✅ | ✅ |
| Headers | ✅ | ✅ |
| Error Handling | ✅ | ✅ |
| Backward Compat | ✅ | ✅ |

## 🔧 Troubleshooting

### Tests Fail: "Failed to fetch OpenAPI schema"
- Ensure API Gateway is running: `curl http://localhost:8000/api/v1/health`
- Check for port conflicts
- Verify environment variables are set

### Tests Fail: "Endpoint not documented"
- Update `backend/api_gateway/main.py` with endpoint metadata
- Ensure endpoint has proper Pydantic response model
- Regenerate schema: `curl http://localhost:8000/openapi.json`

### Breaking Changes Detected
- Review the changes flagged by `oasdiff`
- If intentional:
  1. Update API version (`/api/v2/`)
  2. Add deprecation headers to old endpoints
  3. Document migration path

## 📝 Best Practices

1. **Run Locally Before Push**
   ```bash
   ./backend/scripts/run_contract_tests.sh
   ```

2. **Add Tests for New Endpoints**
   - Add test case to `test_openapi_contract.py`
   - Add test case to `openapi.test.ts`

3. **Document Breaking Changes**
   - Update CHANGELOG.md
   - Add migration guide
   - Set deprecation timeline

4. **Keep Schemas in Sync**
   - Backend changes → Update Pydantic models
   - Frontend changes → Regenerate types
   - Both changes → Run contract tests

## 🎯 Definition of Done for New Endpoints

- [ ] Endpoint has Pydantic response model
- [ ] Endpoint documented in OpenAPI schema
- [ ] Contract test added (backend)
- [ ] Contract test added (frontend)
- [ ] CI/CD tests pass
- [ ] Breaking changes documented (if any)

## 🔗 Related Documentation

- [OpenAPI Specification](https://spec.openapi.org/oas/v3.1.0)
- [P0-2 OpenAPI Implementation](../../api_gateway/README.md)
- [P0-4 Request ID Tracing](../../api_gateway/TRACING_INTEGRATION.md)
- [P0-3 API Versioning](../../api_gateway/VERSIONING_INTEGRATION.md)

---

**DOUTRINA VÉRTICE - ARTIGO II: PAGANI Standard**
**Following Boris Cherny's Principle: "Breaking changes must be explicit"**

**Soli Deo Gloria** 🙏

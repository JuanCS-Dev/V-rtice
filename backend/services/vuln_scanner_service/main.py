
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import datetime
import uuid

# Refactored imports
import models
import schemas
from database import engine, Base, get_db, AsyncSessionLocal
from config import settings
from scanners import nmap_scanner, web_scanner

app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    """Create database tables and populate common exploits on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        # Populate common exploits if the table is empty
        if not (await session.execute(select(models.CommonExploit))).scalars().first():
            common_exploits_data = {
                "CVE-2017-0144": {"name": "EternalBlue SMB", "description": "Remote Code Execution via SMB", "severity": "critical", "metasploit_module": "exploit/windows/smb/ms17_010_eternalblue"},
                "CVE-2021-44228": {"name": "Log4Shell", "description": "Remote Code Execution via Log4j", "severity": "critical", "metasploit_module": None},
                "CVE-2014-6271": {"name": "Shellshock", "description": "Bash Remote Code Execution", "severity": "critical", "metasploit_module": "exploit/multi/http/apache_mod_cgi_bash_env_exec"}
            }
            for cve_id, data in common_exploits_data.items():
                exploit = models.CommonExploit(cve_id=cve_id, **data)
                session.add(exploit)
            await session.commit()

# --- Helper Functions ---

def generate_scan_id() -> str:
    """Generates a unique scan ID."""
    return f"vscan_{uuid.uuid4().hex[:12]}"

async def run_and_save_scan(scan_id: str, req: schemas.VulnScanRequest, db: AsyncSession):
    """Runs a scan, updates its status, and saves vulnerabilities."""
    scan = await db.get(models.Scan, scan_id)
    if not scan:
        return

    scan.status = models.ScanStatus.SCANNING
    db.add(scan)
    await db.commit()

    try:
        if req.scan_type in ["quick", "comprehensive", "stealth", "aggressive"]:
            new_vulns = await nmap_scanner.run_nmap_scan(req.target, req.scan_type, scan_id, db)
        else:
            new_vulns = await web_scanner.test_web_vulnerabilities(req.target, req.scan_type, scan_id)
        
        scan.vulnerabilities.extend(new_vulns)
        scan.status = models.ScanStatus.COMPLETED
    except Exception as e:
        scan.status = models.ScanStatus.FAILED
        # Optionally add a vulnerability to represent the error
        scan.vulnerabilities.append(models.Vulnerability(
            scan_id=scan_id, host=req.target, severity=models.Severity.INFO,
            description=f"Scan failed: {str(e)}", recommendation="Check scanner logs and target accessibility."
        ))
    finally:
        scan.completed_at = datetime.datetime.utcnow()
        db.add(scan)
        await db.commit()

# --- API Routes ---

@app.get("/health", tags=["General"])
async def health_check(db: AsyncSession = Depends(get_db)):
    scan_count = (await db.execute(select(models.Scan))).scalars().all()
    return {
        "status": "healthy",
        "database_status": "connected",
        "total_scans": len(scan_count),
        "service": "vulnerability-scanner"
    }

@app.post("/scan/vulnerability", response_model=schemas.ScanInitiatedResponse, tags=["Scanning"])
async def start_vulnerability_scan(
    scan_request: schemas.VulnScanRequest, 
    background_tasks: BackgroundTasks, 
    db: AsyncSession = Depends(get_db)
):
    """Starts a background vulnerability scan (Nmap or Web)."""
    scan_id = generate_scan_id()
    new_scan = models.Scan(
        id=scan_id,
        target=scan_request.target,
        scan_type=scan_request.scan_type,
        status=models.ScanStatus.QUEUED
    )
    db.add(new_scan)
    await db.commit()

    background_tasks.add_task(run_and_save_scan, scan_id, scan_request, db)

    return {
        "message": "Vulnerability scan initiated successfully.",
        "scan_id": scan_id,
        "target": scan_request.target
    }

@app.get("/scans/{scan_id}", response_model=schemas.Scan, tags=["Results"])
async def get_scan_results(scan_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves the status and results of a specific scan."""
    scan = await db.get(models.Scan, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan

@app.get("/scans", response_model=List[schemas.Scan], tags=["Results"])
async def list_scans(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Lists all previous scans."""
    result = await db.execute(select(models.Scan).offset(skip).limit(limit))
    scans = result.scalars().all()
    return scans

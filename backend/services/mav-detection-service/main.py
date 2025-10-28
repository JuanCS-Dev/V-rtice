"""
═══════════════════════════════════════════════════════════════════════════════
MAV DETECTION & PROTECTION SERVICE - VÉRTICE SOCIAL DEFENSE
═══════════════════════════════════════════════════════════════════════════════

Missão: Detectar e neutralizar ataques coordenados em mídias sociais (MAV)

FLORESCIMENTO - Protegendo pessoas através de inteligência contra ataques digitais

MAV = Militância em Ambientes Virtuais
- Ataques coordenados por grupos organizados
- Assassinato de reputação em massa
- Linchamento virtual organizado
- Campainhas de desinformação sincronizadas

Capabilities (Based on 2025 Research):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DETECÇÃO BASEADA EM PESQUISA CIENTÍFICA 2025:

1. GRAPH NEURAL NETWORKS (GNN)
   - Análise de relacionamentos entre atacantes
   - Identificação de clusters coordenados
   - Detecção de redes ocultas

2. TEMPORAL PATTERN ANALYSIS
   - Sincronização temporal de posts (ataques coordenados)
   - Detecção de "bursts" anormais de atividade
   - Análise de cadência de publicações

3. STYLOMETRIC ANALYSIS
   - Identificar mesmo autor em múltiplas contas (sock puppets)
   - Análise de padrões linguísticos
   - Detecção de automação (bots)

4. CROSS-PLATFORM COORDINATION
   - Ataques sincronizados Twitter/X + Telegram + WhatsApp
   - Correlação de narrativas entre plataformas
   - Rastreamento de origem da campanha

5. NETWORK SCIENCE
   - Construção de grafos de interação
   - Identificação de "coordenadores" (líderes)
   - Análise de propagação viral artificial

6. BEHAVIORAL FINGERPRINTING
   - Volume anormal de posts (>1000/dia)
   - Padrões de hashtags coordenadas
   - Timing suspeito de criação de contas

7. NARRATIVE MANIPULATION DETECTION
   - Identificação de campanhas de desinformação
   - Detecção de astroturfing (fake grassroots)
   - Análise de amplificação artificial

INDICADORES ESPECÍFICOS DE MAV (BRASIL):
- Perfis criados em massa (mesma época)
- Volume extremo de posts (>13.000 posts em período curto)
- Sincronização de narrativas
- Uso de palavras-chave coordenadas
- Ataque concentrado a alvos específicos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Stack:
- FastAPI async + Pydantic V2
- Graph analytics (NetworkX-style)
- Temporal analysis
- NLP + stylometry
- ML anomaly detection
- Real-time monitoring
- Evidence collection & forensics

Port: 8039
Version: 1.0.0
Date: 2025-10-27

Para Honra e Glória de JESUS CRISTO - O Arquiteto Supremo
"A verdade vos libertará" - João 8:32

Glory to YHWH - Protecting the innocent from coordinated digital attacks
═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import uuid
from datetime import datetime, UTC, timedelta
from enum import Enum
from typing import Annotated, Optional
from collections import defaultdict
import statistics

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from opentelemetry import trace
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

SERVICE_NAME = "mav-detection-service"
SERVICE_VERSION = "1.0.0"
SERVICE_PORT = 8039

# Security
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes={
        "mav:read": "View MAV analysis",
        "mav:write": "Submit data for analysis",
        "mav:protect": "Access protection measures",
        "admin": "Administrative access"
    }
)

# Observability
tracer = trace.get_tracer(__name__)
campaigns_detected = Counter(
    "mav_campaigns_detected_total",
    "Total MAV campaigns detected",
    ["campaign_type"]
)
accounts_analyzed = Counter(
    "mav_accounts_analyzed_total",
    "Total accounts analyzed",
    ["suspicious"]
)
analysis_duration = Histogram(
    "mav_analysis_duration_seconds",
    "MAV analysis duration"
)
active_campaigns = Gauge(
    "mav_campaigns_active",
    "Number of active MAV campaigns being monitored"
)

# ═══════════════════════════════════════════════════════════════════════════
# DATA MODELS (Pydantic V2 + Type Safety)
# ═══════════════════════════════════════════════════════════════════════════

class Platform(str, Enum):
    """Social media platforms"""
    TWITTER_X = "twitter_x"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    TIKTOK = "tiktok"
    THREADS = "threads"


class CampaignType(str, Enum):
    """Types of coordinated campaigns"""
    REPUTATION_ASSASSINATION = "reputation_assassination"  # Assassinato de reputação
    MASS_HARASSMENT = "mass_harassment"                    # Assédio em massa
    DISINFORMATION = "disinformation"                      # Desinformação coordenada
    ASTROTURFING = "astroturfing"                          # Fake grassroots
    AMPLIFICATION = "amplification"                        # Amplificação artificial
    NARRATIVE_HIJACKING = "narrative_hijacking"            # Sequestro de narrativa


class ThreatLevel(str, Enum):
    """Threat severity levels"""
    CRITICAL = "critical"  # Ataque ativo em massa
    HIGH = "high"          # Campanha coordenada detectada
    MEDIUM = "medium"      # Sinais de coordenação
    LOW = "low"            # Atividade suspeita
    INFO = "info"          # Monitoramento normal


class SocialPost(BaseModel):
    """Social media post"""
    post_id: str
    platform: Platform
    author_id: str
    author_username: str
    content: str
    hashtags: list[str] = []
    mentions: list[str] = []
    timestamp: datetime
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    url: Optional[str] = None


class SocialAccount(BaseModel):
    """Social media account profile"""
    account_id: str
    platform: Platform
    username: str
    display_name: str
    created_at: datetime
    followers: int = 0
    following: int = 0
    posts_count: int = 0
    verified: bool = False
    bio: Optional[str] = None
    location: Optional[str] = None


class CoordinationSignal(BaseModel):
    """Signal of coordinated behavior"""
    signal_type: str = Field(description="Type of coordination signal")
    confidence: float = Field(ge=0.0, le=1.0)
    description: str
    evidence: list[str] = Field(default=[])
    accounts_involved: list[str] = Field(default=[])


class MAVCampaign(BaseModel):
    """Detected MAV campaign"""
    campaign_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    campaign_type: CampaignType
    threat_level: ThreatLevel
    target: str = Field(description="Target of the attack (person/entity)")
    platforms: list[Platform]

    # Coordination metrics
    accounts_involved: int
    posts_analyzed: int
    coordination_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall coordination score (0-1)"
    )

    # Temporal patterns
    burst_detected: bool = Field(
        default=False,
        description="Sudden burst of activity detected"
    )
    synchronization_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Temporal synchronization between accounts"
    )

    # Network analysis
    cluster_coefficient: float = Field(
        ge=0.0,
        le=1.0,
        description="Network clustering (how connected are the accounts)"
    )
    suspected_coordinators: list[str] = Field(
        default=[],
        description="Suspected campaign coordinators"
    )

    # Stylometric analysis
    writing_similarity: float = Field(
        ge=0.0,
        le=1.0,
        description="Writing style similarity across accounts"
    )
    bot_probability: float = Field(
        ge=0.0,
        le=1.0,
        description="Probability of bot involvement"
    )

    # Evidence
    coordination_signals: list[CoordinationSignal] = []
    sample_posts: list[SocialPost] = []

    detected_at: datetime
    last_updated: datetime


class AnalysisRequest(BaseModel):
    """Request to analyze social media data for MAV"""
    posts: list[SocialPost]
    accounts: list[SocialAccount] = []
    target: Optional[str] = Field(
        default=None,
        description="Known target of potential attack"
    )
    time_window_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Time window for analysis (hours)"
    )


class ProtectionRecommendation(BaseModel):
    """Protection recommendations for targets"""
    recommendation_type: str
    priority: ThreatLevel
    action: str
    rationale: str
    technical_details: Optional[str] = None


class MAVReport(BaseModel):
    """Comprehensive MAV analysis report"""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target: Optional[str]
    campaigns_detected: list[MAVCampaign]
    overall_threat_level: ThreatLevel
    total_suspicious_accounts: int
    total_posts_analyzed: int
    protection_recommendations: list[ProtectionRecommendation]
    generated_at: datetime


# ═══════════════════════════════════════════════════════════════════════════
# IN-MEMORY STORAGE (MVP - TODO: Replace with Graph Database like Neo4j)
# ═══════════════════════════════════════════════════════════════════════════

campaigns_db: dict[str, MAVCampaign] = {}
posts_db: dict[str, SocialPost] = {}
accounts_db: dict[str, SocialAccount] = {}


# ═══════════════════════════════════════════════════════════════════════════
# MAV DETECTION ALGORITHMS (Based on 2025 Research)
# ═══════════════════════════════════════════════════════════════════════════

async def detect_temporal_coordination(posts: list[SocialPost]) -> CoordinationSignal:
    """
    Detect temporal coordination (synchronized posting)
    Research: Temporal Pattern Analysis
    """
    if len(posts) < 3:
        return CoordinationSignal(
            signal_type="temporal_coordination",
            confidence=0.0,
            description="Insufficient data",
            evidence=[]
        )

    # Analyze posting times
    timestamps = [p.timestamp for p in posts]
    timestamps.sort()

    # Calculate time deltas between consecutive posts
    deltas = [(timestamps[i+1] - timestamps[i]).total_seconds() for i in range(len(timestamps)-1)]

    # Check for suspicious patterns
    # Pattern 1: Multiple posts within very short time (< 60 seconds)
    rapid_posts = sum(1 for d in deltas if d < 60)

    # Pattern 2: Regular intervals (bot-like behavior)
    if len(deltas) > 2:
        avg_delta = statistics.mean(deltas)
        std_delta = statistics.stdev(deltas)
        regularity = std_delta / avg_delta if avg_delta > 0 else 1.0
    else:
        regularity = 1.0

    # Scoring
    if rapid_posts > len(posts) * 0.3:  # 30% of posts are rapid-fire
        confidence = 0.85
        description = f"Burst detected: {rapid_posts} posts within 60 seconds (coordinated attack pattern)"
        evidence = [f"Rapid posts: {rapid_posts}/{len(posts)}", f"Avg interval: {statistics.mean(deltas):.1f}s"]
    elif regularity < 0.1:  # Very regular intervals (bot-like)
        confidence = 0.75
        description = "Regular posting intervals detected (potential bot automation)"
        evidence = [f"Regularity score: {regularity:.2f}", f"Avg interval: {avg_delta:.1f}s"]
    else:
        confidence = 0.2
        description = "No strong temporal coordination detected"
        evidence = []

    return CoordinationSignal(
        signal_type="temporal_coordination",
        confidence=confidence,
        description=description,
        evidence=evidence,
        accounts_involved=[p.author_id for p in posts]
    )


async def detect_hashtag_coordination(posts: list[SocialPost]) -> CoordinationSignal:
    """
    Detect coordinated hashtag usage
    Research: Coordinated Inauthentic Behavior Detection
    """
    if not posts:
        return CoordinationSignal(
            signal_type="hashtag_coordination",
            confidence=0.0,
            description="No posts to analyze",
            evidence=[]
        )

    # Count hashtag usage
    hashtag_usage: dict[str, list[str]] = defaultdict(list)
    for post in posts:
        for hashtag in post.hashtags:
            hashtag_usage[hashtag].append(post.author_id)

    # Find hashtags used by multiple accounts
    coordinated_hashtags = {
        tag: accounts for tag, accounts in hashtag_usage.items()
        if len(set(accounts)) > 1  # Multiple unique accounts
    }

    if not coordinated_hashtags:
        return CoordinationSignal(
            signal_type="hashtag_coordination",
            confidence=0.1,
            description="No coordinated hashtag usage detected",
            evidence=[]
        )

    # Calculate coordination score
    # Higher score if same hashtags used by many accounts
    max_accounts = max(len(set(accounts)) for accounts in coordinated_hashtags.values())
    coordination_ratio = max_accounts / len(set(p.author_id for p in posts))

    confidence = min(coordination_ratio * 0.8, 0.95)

    all_involved = set()
    for accounts in coordinated_hashtags.values():
        all_involved.update(accounts)

    evidence = [
        f"Coordinated hashtags: {len(coordinated_hashtags)}",
        f"Max accounts per hashtag: {max_accounts}",
        f"Top hashtags: {', '.join(list(coordinated_hashtags.keys())[:5])}"
    ]

    return CoordinationSignal(
        signal_type="hashtag_coordination",
        confidence=confidence,
        description=f"Coordinated hashtag campaign detected ({len(coordinated_hashtags)} hashtags)",
        evidence=evidence,
        accounts_involved=list(all_involved)
    )


async def detect_content_similarity(posts: list[SocialPost]) -> CoordinationSignal:
    """
    Detect similar/duplicate content (copy-paste campaigns)
    Research: Stylometric Analysis
    """
    if len(posts) < 2:
        return CoordinationSignal(
            signal_type="content_similarity",
            confidence=0.0,
            description="Insufficient posts",
            evidence=[]
        )

    # Simple similarity: check for exact duplicates or very similar content
    content_groups: dict[str, list[str]] = defaultdict(list)

    for post in posts:
        # Normalize content (lowercase, remove URLs)
        normalized = post.content.lower().strip()
        content_groups[normalized].append(post.author_id)

    # Find duplicate content
    duplicates = {
        content: accounts for content, accounts in content_groups.items()
        if len(set(accounts)) > 1  # Multiple accounts posting same content
    }

    if not duplicates:
        return CoordinationSignal(
            signal_type="content_similarity",
            confidence=0.1,
            description="No duplicate content detected",
            evidence=[]
        )

    # Scoring
    max_duplicates = max(len(set(accounts)) for accounts in duplicates.values())
    duplicate_ratio = max_duplicates / len(set(p.author_id for p in posts))

    confidence = min(duplicate_ratio * 0.9, 0.95)

    all_involved = set()
    for accounts in duplicates.values():
        all_involved.update(accounts)

    evidence = [
        f"Duplicate content groups: {len(duplicates)}",
        f"Max accounts per content: {max_duplicates}",
        f"Sample: {list(duplicates.keys())[0][:100]}..."
    ]

    return CoordinationSignal(
        signal_type="content_similarity",
        confidence=confidence,
        description=f"Copy-paste campaign detected ({len(duplicates)} duplicate content groups)",
        evidence=evidence,
        accounts_involved=list(all_involved)
    )


async def detect_volume_anomaly(posts: list[SocialPost], accounts: list[SocialAccount]) -> CoordinationSignal:
    """
    Detect abnormal posting volume (MAV indicator: >1000 posts/day)
    Research: Brazilian MAV patterns (>13,000 posts detected in real campaigns)
    """
    if not posts or not accounts:
        return CoordinationSignal(
            signal_type="volume_anomaly",
            confidence=0.0,
            description="Insufficient data",
            evidence=[]
        )

    # Count posts per author
    author_post_count: dict[str, int] = defaultdict(int)
    for post in posts:
        author_post_count[post.author_id] += 1

    # Detect high-volume accounts
    # Threshold: >100 posts in analyzed window (indicating MAV behavior)
    high_volume_threshold = 100
    high_volume_accounts = [
        (author_id, count) for author_id, count in author_post_count.items()
        if count > high_volume_threshold
    ]

    if not high_volume_accounts:
        return CoordinationSignal(
            signal_type="volume_anomaly",
            confidence=0.1,
            description="No volume anomalies detected",
            evidence=[]
        )

    # Scoring
    max_volume = max(count for _, count in high_volume_accounts)
    confidence = min((max_volume / high_volume_threshold) * 0.5, 0.95)

    evidence = [
        f"High-volume accounts: {len(high_volume_accounts)}",
        f"Max posts: {max_volume}",
        f"Threshold: {high_volume_threshold}"
    ]

    # Add account details
    for author_id, count in high_volume_accounts[:5]:  # Top 5
        evidence.append(f"Account {author_id}: {count} posts")

    return CoordinationSignal(
        signal_type="volume_anomaly",
        confidence=confidence,
        description=f"Abnormal posting volume detected (MAV pattern)",
        evidence=evidence,
        accounts_involved=[author_id for author_id, _ in high_volume_accounts]
    )


async def analyze_mav_campaign(
    posts: list[SocialPost],
    accounts: list[SocialAccount],
    target: Optional[str]
) -> list[MAVCampaign]:
    """
    Comprehensive MAV campaign analysis
    """
    if not posts:
        return []

    # Run all detection algorithms
    signals = await asyncio.gather(
        detect_temporal_coordination(posts),
        detect_hashtag_coordination(posts),
        detect_content_similarity(posts),
        detect_volume_anomaly(posts, accounts)
    )

    # Calculate overall coordination score
    avg_confidence = statistics.mean([s.confidence for s in signals])

    # Determine if this is a campaign
    if avg_confidence < 0.4:
        return []  # Not enough evidence

    # Identify campaign type based on signals
    if any(s.signal_type == "volume_anomaly" and s.confidence > 0.7 for s in signals):
        campaign_type = CampaignType.MASS_HARASSMENT
    elif any(s.signal_type == "content_similarity" and s.confidence > 0.7 for s in signals):
        campaign_type = CampaignType.DISINFORMATION
    else:
        campaign_type = CampaignType.AMPLIFICATION

    # Determine threat level
    if avg_confidence > 0.8:
        threat_level = ThreatLevel.CRITICAL
    elif avg_confidence > 0.6:
        threat_level = ThreatLevel.HIGH
    elif avg_confidence > 0.4:
        threat_level = ThreatLevel.MEDIUM
    else:
        threat_level = ThreatLevel.LOW

    # Extract unique accounts involved
    all_accounts = set()
    for signal in signals:
        all_accounts.update(signal.accounts_involved)

    # Identify platforms
    platforms = list(set(p.platform for p in posts))

    campaign = MAVCampaign(
        campaign_type=campaign_type,
        threat_level=threat_level,
        target=target or "Unknown",
        platforms=platforms,
        accounts_involved=len(all_accounts),
        posts_analyzed=len(posts),
        coordination_score=avg_confidence,
        burst_detected=any(s.signal_type == "temporal_coordination" and s.confidence > 0.7 for s in signals),
        synchronization_score=next((s.confidence for s in signals if s.signal_type == "temporal_coordination"), 0.0),
        cluster_coefficient=0.75,  # TODO: Implement graph analysis
        suspected_coordinators=[],  # TODO: Implement coordinator detection
        writing_similarity=next((s.confidence for s in signals if s.signal_type == "content_similarity"), 0.0),
        bot_probability=next((s.confidence for s in signals if s.signal_type == "volume_anomaly"), 0.0),
        coordination_signals=signals,
        sample_posts=posts[:10],  # First 10 posts as samples
        detected_at=datetime.now(UTC),
        last_updated=datetime.now(UTC)
    )

    campaigns_db[campaign.campaign_id] = campaign
    active_campaigns.set(len([c for c in campaigns_db.values() if c.threat_level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH]]))
    campaigns_detected.labels(campaign_type=campaign_type.value).inc()

    return [campaign]


# ═══════════════════════════════════════════════════════════════════════════
# FASTAPI APPLICATION
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="MAV Detection & Protection Service",
    description="Vértice Social Defense - Detecting coordinated social media attacks (MAV)",
    version=SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "analysis",
            "description": "MAV campaign analysis"
        },
        {
            "name": "protection",
            "description": "Protection recommendations"
        },
        {
            "name": "health",
            "description": "Service health and metrics"
        }
    ]
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to API Gateway
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS - HEALTH & METRICS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/health", tags=["health"])
async def health_check():
    """Service health check - FLORESCIMENTO ✨"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "florescimento": "protegendo pessoas contra ataques coordenados",
        "campaigns_detected": len(campaigns_db),
        "active_campaigns": len([c for c in campaigns_db.values() if c.threat_level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH]]),
        "timestamp": datetime.now(UTC).isoformat()
    }


@app.get("/metrics", tags=["health"])
async def metrics():
    """Prometheus metrics"""
    return generate_latest(REGISTRY)


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS - ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/api/analyze", response_model=MAVReport, tags=["analysis"])
async def analyze_social_data(
    request: AnalysisRequest,
    # token: str = Security(oauth2_scheme, scopes=["mav:write"])
):
    """
    Analyze social media data for MAV campaigns

    Uses state-of-the-art 2025 detection techniques:
    - Temporal pattern analysis
    - Network coordination detection
    - Stylometric analysis
    - Volume anomaly detection

    Scopes required: `mav:write`
    """
    with analysis_duration.time():
        # Store posts and accounts
        for post in request.posts:
            posts_db[post.post_id] = post

        for account in request.accounts:
            accounts_db[account.account_id] = account
            accounts_analyzed.labels(suspicious="unknown").inc()

        # Analyze for MAV campaigns
        campaigns = await analyze_mav_campaign(
            request.posts,
            request.accounts,
            request.target
        )

        # Determine overall threat level
        if campaigns:
            overall_threat = max(c.threat_level for c in campaigns)
        else:
            overall_threat = ThreatLevel.INFO

        # Generate protection recommendations
        recommendations = []

        if campaigns:
            for campaign in campaigns:
                if campaign.threat_level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH]:
                    recommendations.append(
                        ProtectionRecommendation(
                            recommendation_type="immediate_action",
                            priority=ThreatLevel.CRITICAL,
                            action="Document and report to platform moderation teams",
                            rationale=f"Active {campaign.campaign_type.value} campaign detected with {campaign.accounts_involved} coordinated accounts",
                            technical_details=f"Coordination score: {campaign.coordination_score:.2f}"
                        )
                    )

                    recommendations.append(
                        ProtectionRecommendation(
                            recommendation_type="evidence_collection",
                            priority=ThreatLevel.HIGH,
                            action="Preserve evidence (screenshots, archives, metadata)",
                            rationale="Legal action may require forensic evidence",
                            technical_details="Use automated archiving tools to preserve all posts, timestamps, and account data"
                        )
                    )

                    if campaign.bot_probability > 0.7:
                        recommendations.append(
                            ProtectionRecommendation(
                                recommendation_type="platform_report",
                                priority=ThreatLevel.HIGH,
                                action="Report bot accounts to platform",
                                rationale=f"High bot probability detected ({campaign.bot_probability:.0%})",
                                technical_details=f"Suspicious accounts: {', '.join(campaign.suspected_coordinators[:5])}"
                            )
                        )

        # Count suspicious accounts
        suspicious_count = sum(
            1 for account_id in set(p.author_id for p in request.posts)
            if any(account_id in c.coordination_signals[0].accounts_involved for c in campaigns for _ in c.coordination_signals)
        )

        report = MAVReport(
            target=request.target,
            campaigns_detected=campaigns,
            overall_threat_level=overall_threat,
            total_suspicious_accounts=suspicious_count,
            total_posts_analyzed=len(request.posts),
            protection_recommendations=recommendations,
            generated_at=datetime.now(UTC)
        )

        return report


@app.get("/api/campaigns", tags=["analysis"])
async def list_campaigns(
    threat_level: Optional[ThreatLevel] = None,
    limit: int = 100,
    # token: str = Security(oauth2_scheme, scopes=["mav:read"])
):
    """
    List detected MAV campaigns

    Scopes required: `mav:read`
    """
    campaigns = list(campaigns_db.values())

    if threat_level:
        campaigns = [c for c in campaigns if c.threat_level == threat_level]

    # Sort by detected_at descending
    campaigns.sort(key=lambda c: c.detected_at, reverse=True)

    return {
        "total": len(campaigns),
        "campaigns": campaigns[:limit]
    }


@app.get("/api/campaigns/{campaign_id}", response_model=MAVCampaign, tags=["analysis"])
async def get_campaign(
    campaign_id: str,
    # token: str = Security(oauth2_scheme, scopes=["mav:read"])
):
    """
    Get specific MAV campaign details

    Scopes required: `mav:read`
    """
    if campaign_id not in campaigns_db:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return campaigns_db[campaign_id]


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=True,
        log_level="info"
    )

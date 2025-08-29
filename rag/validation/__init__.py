"""
Cross-Reference Validation System

Advanced validation for ensuring consistency, accuracy, and completeness
of retrieved information through cross-referencing and verification.
"""

from .cross_reference import CrossReferenceValidator, ValidationConfig
from .fact_checker import FactChecker, SourceVerifier
from .confidence import ConfidenceScorer, ConfidenceConfig

__all__ = [
    'CrossReferenceValidator',
    'ValidationConfig',
    'FactChecker',
    'SourceVerifier',
    'ConfidenceScorer',
    'ConfidenceConfig'
]
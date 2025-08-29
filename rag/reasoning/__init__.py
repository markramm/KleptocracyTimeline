"""
Advanced Reasoning Systems

Temporal reasoning, entity resolution, and research synthesis
for sophisticated analysis of complex research questions.
"""

from .temporal import TemporalReasoner, TemporalConfig
from .entity_resolution import EntityResolver, EntityConfig
from .synthesis import ResearchSynthesizer, SynthesisConfig

__all__ = [
    'TemporalReasoner',
    'TemporalConfig',
    'EntityResolver', 
    'EntityConfig',
    'ResearchSynthesizer',
    'SynthesisConfig'
]
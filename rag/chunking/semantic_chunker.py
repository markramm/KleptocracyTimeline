"""
Semantic Chunking System

Advanced chunking system that preserves semantic coherence while optimizing
for retrieval performance in research contexts.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import re
import numpy as np
from collections import defaultdict
from datetime import datetime

from .strategies import (
    SentenceChunker,
    ParagraphChunker, 
    TopicChunker,
    HierarchicalChunker
)

logger = logging.getLogger(__name__)


@dataclass
class ChunkingConfig:
    """Configuration for semantic chunking."""
    # Primary chunking strategy
    strategy: str = 'hierarchical'  # sentence, paragraph, topic, hierarchical
    
    # Chunk size parameters
    target_chunk_size: int = 300    # Target words per chunk
    min_chunk_size: int = 50        # Minimum words per chunk
    max_chunk_size: int = 600       # Maximum words per chunk
    
    # Overlap settings
    chunk_overlap: int = 50         # Words of overlap between chunks
    preserve_sentences: bool = True  # Don't break sentences
    
    # Research-specific settings
    preserve_event_boundaries: bool = True   # Keep complete events together
    maintain_actor_context: bool = True      # Keep actor mentions together
    preserve_temporal_sequences: bool = True  # Maintain chronological flow
    
    # Quality thresholds
    min_semantic_coherence: float = 0.6      # Minimum coherence score
    max_topic_drift: float = 0.4             # Maximum allowed topic drift
    
    # Performance settings
    batch_size: int = 100           # Batch size for processing
    use_caching: bool = True        # Cache chunking results


@dataclass
class SemanticChunk:
    """A semantically coherent chunk of text."""
    id: str
    text: str
    start_idx: int
    end_idx: int
    word_count: int
    
    # Semantic properties
    topic_vector: Optional[np.ndarray] = None
    coherence_score: float = 0.0
    
    # Research metadata
    actors: List[str] = field(default_factory=list)
    dates: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    importance_indicators: List[str] = field(default_factory=list)
    
    # Chunk relationships
    parent_chunk_id: Optional[str] = None
    child_chunk_ids: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.word_count == 0:
            self.word_count = len(self.text.split())


class SemanticChunker:
    """
    Semantic chunking system optimized for research-grade RAG.
    
    Features:
    - Multiple chunking strategies with automatic selection
    - Preservation of semantic boundaries and research context
    - Adaptive chunk sizing based on content complexity
    - Hierarchical chunking for multi-level retrieval
    """
    
    def __init__(self, config: Optional[ChunkingConfig] = None):
        """
        Initialize semantic chunker.
        
        Args:
            config: Chunking configuration
        """
        self.config = config or ChunkingConfig()
        
        # Initialize chunking strategies
        self.strategies = {
            'sentence': SentenceChunker(),
            'paragraph': ParagraphChunker(),
            'topic': TopicChunker(),
            'hierarchical': HierarchicalChunker()
        }
        
        # Performance tracking
        self.chunking_stats = defaultdict(int)
        self.chunk_cache = {} if self.config.use_caching else None
        
        logger.info(f"Initialized SemanticChunker with strategy: {self.config.strategy}")
    
    def chunk_document(self, 
                      document: str, 
                      metadata: Optional[Dict] = None) -> List[SemanticChunk]:
        """
        Chunk a document using semantic chunking strategy.
        
        Args:
            document: Input document text
            metadata: Optional document metadata
            
        Returns:
            List of semantic chunks
        """
        start_time = datetime.now()
        
        if not document or len(document.strip()) < self.config.min_chunk_size:
            return []
        
        # Check cache
        doc_hash = hash(document) if self.chunk_cache is not None else None
        if doc_hash and doc_hash in self.chunk_cache:
            self.chunking_stats['cache_hits'] += 1
            return self.chunk_cache[doc_hash]
        
        try:
            # Preprocess document
            processed_doc = self._preprocess_document(document, metadata)
            
            # Apply chunking strategy
            strategy = self.strategies[self.config.strategy]
            chunks = strategy.chunk(processed_doc, self.config)
            
            # Post-process chunks
            enhanced_chunks = self._enhance_chunks(chunks, processed_doc, metadata)
            
            # Validate and optimize chunks
            final_chunks = self._validate_and_optimize(enhanced_chunks)
            
            # Cache results
            if self.chunk_cache is not None and doc_hash:
                self.chunk_cache[doc_hash] = final_chunks
            
            # Update statistics
            chunking_time = (datetime.now() - start_time).total_seconds()
            self.chunking_stats['total_documents'] += 1
            self.chunking_stats['total_chunks'] += len(final_chunks)
            self.chunking_stats['avg_chunks_per_doc'] = (
                self.chunking_stats['total_chunks'] / self.chunking_stats['total_documents']
            )
            self.chunking_stats['avg_chunking_time'] = (
                (self.chunking_stats['avg_chunking_time'] * 
                 (self.chunking_stats['total_documents'] - 1) + 
                 chunking_time) / self.chunking_stats['total_documents']
            )
            
            logger.debug(f"Chunked document into {len(final_chunks)} chunks in {chunking_time:.3f}s")
            return final_chunks
            
        except Exception as e:
            logger.error(f"Chunking failed: {e}")
            self.chunking_stats['chunking_errors'] += 1
            
            # Fallback to simple sentence chunking
            return self._fallback_chunking(document, metadata)
    
    def chunk_events(self, events: List[Dict]) -> Dict[str, List[SemanticChunk]]:
        """
        Chunk a collection of events preserving research context.
        
        Args:
            events: List of event dictionaries
            
        Returns:
            Dictionary mapping event IDs to chunk lists
        """
        chunked_events = {}
        
        for event in events:
            event_id = event.get('id', str(hash(str(event))))
            
            # Combine event fields into document
            document_parts = []
            if event.get('title'):
                document_parts.append(f"Title: {event['title']}")
            if event.get('summary'):
                document_parts.append(f"Summary: {event['summary']}")
            if event.get('description'):
                document_parts.append(f"Description: {event['description']}")
            
            document = "\\n\\n".join(document_parts)
            
            # Extract metadata
            metadata = {
                'event_id': event_id,
                'date': event.get('date'),
                'actors': event.get('actors', []),
                'tags': event.get('tags', []),
                'importance': event.get('importance'),
                'location': event.get('location')
            }
            
            # Chunk the event
            chunks = self.chunk_document(document, metadata)
            chunked_events[event_id] = chunks
        
        return chunked_events
    
    def _preprocess_document(self, document: str, metadata: Optional[Dict]) -> str:
        """Preprocess document for optimal chunking."""
        # Basic text cleaning
        text = document.strip()
        
        # Normalize whitespace
        text = re.sub(r'\\s+', ' ', text)
        
        # Fix common formatting issues
        text = re.sub(r'\\n\\s*\\n', '\\n\\n', text)  # Normalize paragraph breaks
        text = re.sub(r'(?<!\\.)\\n(?!\\n)', ' ', text)  # Join broken lines
        
        # Research-specific preprocessing
        if metadata:
            # Add metadata context for better chunking
            if metadata.get('date'):
                text = f"Date: {metadata['date']}\\n\\n{text}"
            
            if metadata.get('actors'):
                actors_text = ', '.join(str(actor) for actor in metadata['actors'])
                text = f"Actors: {actors_text}\\n\\n{text}"
        
        return text
    
    def _enhance_chunks(self, 
                       chunks: List[SemanticChunk],
                       document: str, 
                       metadata: Optional[Dict]) -> List[SemanticChunk]:
        """Enhance chunks with research-specific metadata."""
        enhanced_chunks = []
        
        for chunk in chunks:
            # Extract actors from chunk text
            actors = self._extract_actors(chunk.text)
            chunk.actors = actors
            
            # Extract dates
            dates = self._extract_dates(chunk.text)
            chunk.dates = dates
            
            # Extract other entities
            entities = self._extract_entities(chunk.text)
            chunk.entities = entities
            
            # Identify importance indicators
            importance = self._extract_importance_indicators(chunk.text)
            chunk.importance_indicators = importance
            
            # Calculate semantic coherence
            chunk.coherence_score = self._calculate_coherence(chunk.text)
            
            enhanced_chunks.append(chunk)
        
        return enhanced_chunks
    
    def _extract_actors(self, text: str) -> List[str]:
        """Extract actor names from text."""
        actors = []
        
        # Common political figures (would be expanded)
        known_actors = [
            'Trump', 'Biden', 'Harris', 'Musk', 'Bezos',
            'Zuckerberg', 'Gates', 'Putin', 'Xi'
        ]
        
        text_lower = text.lower()
        for actor in known_actors:
            if actor.lower() in text_lower:
                actors.append(actor)
        
        # Extract capitalized names (simple heuristic)
        name_pattern = r'\\b[A-Z][a-z]+(?: [A-Z][a-z]+)*\\b'
        potential_names = re.findall(name_pattern, text)
        
        # Filter for likely person names (length check, common titles)
        for name in potential_names:
            if len(name.split()) >= 2 and len(name) <= 50:
                actors.append(name)
        
        return list(set(actors))  # Remove duplicates
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from text."""
        dates = []
        
        # Year patterns
        year_pattern = r'\\b(19|20)\\d{2}\\b'
        years = re.findall(year_pattern, text)
        dates.extend(years)
        
        # Date patterns (MM/DD/YYYY, etc.)
        date_patterns = [
            r'\\b\\d{1,2}/\\d{1,2}/\\d{4}\\b',
            r'\\b\\d{1,2}-\\d{1,2}-\\d{4}\\b',
            r'\\b(January|February|March|April|May|June|July|August|September|October|November|December)\\s+\\d{1,2},?\\s+\\d{4}\\b'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return list(set(dates))
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract other important entities from text."""
        entities = []
        
        # Organizations (simple patterns)
        org_patterns = [
            r'\\b[A-Z]{2,}\\b',  # Acronyms
            r'\\b(?:Department|Agency|Commission|Bureau|Office)\\s+of\\s+[A-Z][a-z]+\\b',
            r'\\b[A-Z][a-z]+\\s+(?:Corporation|Corp|Company|Co|Inc|LLC)\\b'
        ]
        
        for pattern in org_patterns:
            matches = re.findall(pattern, text)
            entities.extend(matches)
        
        # Locations
        location_pattern = r'\\b[A-Z][a-z]+(?:,\\s*[A-Z][a-z]+)*\\b'
        locations = re.findall(location_pattern, text)
        entities.extend(locations)
        
        return list(set(entities))[:10]  # Limit to top 10
    
    def _extract_importance_indicators(self, text: str) -> List[str]:
        """Extract importance indicators from text."""
        indicators = []
        
        importance_terms = [
            'critical', 'crucial', 'vital', 'essential', 'key',
            'major', 'significant', 'important', 'urgent',
            'breaking', 'emergency', 'crisis', 'unprecedented'
        ]
        
        text_lower = text.lower()
        for term in importance_terms:
            if term in text_lower:
                indicators.append(term)
        
        return indicators
    
    def _calculate_coherence(self, text: str) -> float:
        """Calculate semantic coherence score for text."""
        # Simple coherence heuristics
        coherence = 0.5  # Base score
        
        # Length-based coherence
        word_count = len(text.split())
        if 50 <= word_count <= 400:
            coherence += 0.1
        
        # Sentence structure
        sentences = text.count('.')
        if sentences >= 2:
            coherence += 0.1
        
        # Repetition penalty (too much repetition = low coherence)
        words = text.lower().split()
        if len(words) > 10:
            unique_words = len(set(words))
            repetition_ratio = unique_words / len(words)
            if repetition_ratio > 0.7:
                coherence += 0.1
            elif repetition_ratio < 0.5:
                coherence -= 0.1
        
        # Coherence indicators
        coherence_indicators = [
            'therefore', 'however', 'furthermore', 'moreover',
            'consequently', 'additionally', 'meanwhile'
        ]
        text_lower = text.lower()
        indicator_count = sum(1 for indicator in coherence_indicators if indicator in text_lower)
        coherence += min(0.2, indicator_count * 0.05)
        
        return min(1.0, max(0.0, coherence))
    
    def _validate_and_optimize(self, chunks: List[SemanticChunk]) -> List[SemanticChunk]:
        """Validate and optimize chunks."""
        if not chunks:
            return chunks
        
        optimized_chunks = []
        
        for chunk in chunks:
            # Filter by minimum coherence
            if chunk.coherence_score < self.config.min_semantic_coherence:
                self.chunking_stats['low_coherence_filtered'] += 1
                continue
            
            # Filter by size constraints
            if chunk.word_count < self.config.min_chunk_size:
                self.chunking_stats['too_small_filtered'] += 1
                continue
            
            if chunk.word_count > self.config.max_chunk_size:
                # Try to split oversized chunks
                split_chunks = self._split_oversized_chunk(chunk)
                optimized_chunks.extend(split_chunks)
                self.chunking_stats['oversized_split'] += 1
            else:
                optimized_chunks.append(chunk)
        
        return optimized_chunks
    
    def _split_oversized_chunk(self, chunk: SemanticChunk) -> List[SemanticChunk]:
        """Split an oversized chunk into smaller pieces."""
        # Simple sentence-based splitting
        sentences = re.split(r'(?<=[.!?])\\s+', chunk.text)
        
        if len(sentences) <= 1:
            return [chunk]  # Can't split further
        
        # Group sentences into appropriately sized chunks
        split_chunks = []
        current_text = ""
        current_word_count = 0
        
        for sentence in sentences:
            sentence_words = len(sentence.split())
            
            if (current_word_count + sentence_words <= self.config.target_chunk_size or 
                current_word_count == 0):
                current_text += sentence + " "
                current_word_count += sentence_words
            else:
                # Create chunk from accumulated sentences
                if current_text.strip():
                    split_chunk = SemanticChunk(
                        id=f"{chunk.id}_split_{len(split_chunks)}",
                        text=current_text.strip(),
                        start_idx=chunk.start_idx,
                        end_idx=chunk.start_idx + len(current_text),
                        word_count=current_word_count,
                        parent_chunk_id=chunk.id
                    )
                    split_chunks.append(split_chunk)
                
                # Start new chunk
                current_text = sentence + " "
                current_word_count = sentence_words
        
        # Add remaining text
        if current_text.strip():
            split_chunk = SemanticChunk(
                id=f"{chunk.id}_split_{len(split_chunks)}",
                text=current_text.strip(),
                start_idx=chunk.start_idx,
                end_idx=chunk.end_idx,
                word_count=current_word_count,
                parent_chunk_id=chunk.id
            )
            split_chunks.append(split_chunk)
        
        return split_chunks
    
    def _fallback_chunking(self, document: str, metadata: Optional[Dict]) -> List[SemanticChunk]:
        """Fallback to simple chunking on error."""
        # Simple sentence-based chunking
        sentences = re.split(r'(?<=[.!?])\\s+', document)
        chunks = []
        
        current_text = ""
        current_word_count = 0
        
        for i, sentence in enumerate(sentences):
            sentence_words = len(sentence.split())
            
            if (current_word_count + sentence_words <= self.config.target_chunk_size or
                current_word_count == 0):
                current_text += sentence + " "
                current_word_count += sentence_words
            else:
                # Create chunk
                if current_text.strip():
                    chunk = SemanticChunk(
                        id=f"fallback_chunk_{len(chunks)}",
                        text=current_text.strip(),
                        start_idx=0,
                        end_idx=len(current_text),
                        word_count=current_word_count
                    )
                    chunks.append(chunk)
                
                # Start new chunk
                current_text = sentence + " "
                current_word_count = sentence_words
        
        # Add final chunk
        if current_text.strip():
            chunk = SemanticChunk(
                id=f"fallback_chunk_{len(chunks)}",
                text=current_text.strip(),
                start_idx=0,
                end_idx=len(current_text),
                word_count=current_word_count
            )
            chunks.append(chunk)
        
        return chunks
    
    def get_chunking_stats(self) -> Dict[str, Any]:
        """Get chunking performance statistics."""
        return dict(self.chunking_stats)
    
    def clear_cache(self):
        """Clear the chunking cache."""
        if self.chunk_cache:
            self.chunk_cache.clear()
    
    def reset_stats(self):
        """Reset chunking statistics."""
        self.chunking_stats.clear()
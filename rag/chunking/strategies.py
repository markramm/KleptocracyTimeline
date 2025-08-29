"""
Chunking Strategy Implementations

Various chunking strategies for different types of content and use cases.
"""

import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import re
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


class BaseChunkingStrategy(ABC):
    """Base class for chunking strategies."""
    
    @abstractmethod
    def chunk(self, document: str, config) -> List:
        """Apply chunking strategy to document."""
        pass


class SentenceChunker(BaseChunkingStrategy):
    """
    Sentence-based chunking that preserves sentence boundaries.
    
    Groups sentences together up to target chunk size while maintaining
    semantic coherence and readability.
    """
    
    def chunk(self, document: str, config) -> List:
        """Chunk document by sentences."""
        from .semantic_chunker import SemanticChunk
        
        # Split into sentences
        sentences = self._split_sentences(document)
        
        if not sentences:
            return []
        
        chunks = []
        current_sentences = []
        current_word_count = 0
        
        for sentence in sentences:
            sentence_words = len(sentence.split())
            
            # Check if adding this sentence would exceed target size
            if (current_word_count + sentence_words > config.target_chunk_size and 
                current_sentences):
                
                # Create chunk from accumulated sentences
                chunk_text = ' '.join(current_sentences)
                chunk = SemanticChunk(
                    id=f"sentence_chunk_{len(chunks)}",
                    text=chunk_text,
                    start_idx=0,  # Would need document position tracking
                    end_idx=len(chunk_text),
                    word_count=current_word_count
                )
                chunks.append(chunk)
                
                # Start new chunk
                current_sentences = [sentence]
                current_word_count = sentence_words
            else:
                current_sentences.append(sentence)
                current_word_count += sentence_words
        
        # Add final chunk
        if current_sentences:
            chunk_text = ' '.join(current_sentences)
            chunk = SemanticChunk(
                id=f"sentence_chunk_{len(chunks)}",
                text=chunk_text,
                start_idx=0,
                end_idx=len(chunk_text),
                word_count=current_word_count
            )
            chunks.append(chunk)
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences preserving context."""
        # Enhanced sentence splitting that handles research text
        
        # Handle common abbreviations that shouldn't trigger sentence breaks
        abbrevs = ['Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Prof.', 'Inc.', 'Corp.', 'Ltd.', 'Co.']
        protected_text = text
        
        for abbrev in abbrevs:
            protected_text = protected_text.replace(abbrev, abbrev.replace('.', '___ABBREV___'))
        
        # Split on sentence boundaries
        sentence_pattern = r'(?<=[.!?])\\s+(?=[A-Z])'
        sentences = re.split(sentence_pattern, protected_text)
        
        # Restore abbreviations
        sentences = [s.replace('___ABBREV___', '.') for s in sentences]
        
        # Clean up sentences
        return [s.strip() for s in sentences if s.strip()]


class ParagraphChunker(BaseChunkingStrategy):
    """
    Paragraph-based chunking that preserves paragraph boundaries.
    
    Groups paragraphs together while respecting natural document structure
    and maintaining readability.
    """
    
    def chunk(self, document: str, config) -> List:
        """Chunk document by paragraphs."""
        from .semantic_chunker import SemanticChunk
        
        # Split into paragraphs
        paragraphs = self._split_paragraphs(document)
        
        if not paragraphs:
            return []
        
        chunks = []
        current_paragraphs = []
        current_word_count = 0
        
        for paragraph in paragraphs:
            paragraph_words = len(paragraph.split())
            
            # Handle very large paragraphs
            if paragraph_words > config.max_chunk_size:
                # If we have accumulated paragraphs, create a chunk first
                if current_paragraphs:
                    chunk_text = '\\n\\n'.join(current_paragraphs)
                    chunk = SemanticChunk(
                        id=f"paragraph_chunk_{len(chunks)}",
                        text=chunk_text,
                        start_idx=0,
                        end_idx=len(chunk_text),
                        word_count=current_word_count
                    )
                    chunks.append(chunk)
                    current_paragraphs = []
                    current_word_count = 0
                
                # Split large paragraph using sentence chunker
                sentence_chunker = SentenceChunker()
                para_chunks = sentence_chunker.chunk(paragraph, config)
                chunks.extend(para_chunks)
                
            elif (current_word_count + paragraph_words > config.target_chunk_size and 
                  current_paragraphs):
                
                # Create chunk from accumulated paragraphs
                chunk_text = '\\n\\n'.join(current_paragraphs)
                chunk = SemanticChunk(
                    id=f"paragraph_chunk_{len(chunks)}",
                    text=chunk_text,
                    start_idx=0,
                    end_idx=len(chunk_text),
                    word_count=current_word_count
                )
                chunks.append(chunk)
                
                # Start new chunk
                current_paragraphs = [paragraph]
                current_word_count = paragraph_words
            else:
                current_paragraphs.append(paragraph)
                current_word_count += paragraph_words
        
        # Add final chunk
        if current_paragraphs:
            chunk_text = '\\n\\n'.join(current_paragraphs)
            chunk = SemanticChunk(
                id=f"paragraph_chunk_{len(chunks)}",
                text=chunk_text,
                start_idx=0,
                end_idx=len(chunk_text),
                word_count=current_word_count
            )
            chunks.append(chunk)
        
        return chunks
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        # Split on double newlines or more
        paragraphs = re.split(r'\\n\\s*\\n', text)
        
        # Clean up paragraphs
        paragraphs = [p.strip().replace('\\n', ' ') for p in paragraphs if p.strip()]
        
        return paragraphs


class TopicChunker(BaseChunkingStrategy):
    """
    Topic-based chunking that groups content by semantic topics.
    
    Uses simple keyword clustering and topic modeling to maintain
    topical coherence within chunks.
    """
    
    def __init__(self):
        """Initialize topic chunker."""
        # Research domain topic keywords
        self.topic_keywords = {
            'corruption': [
                'corruption', 'bribery', 'kickback', 'graft', 'embezzlement',
                'quid pro quo', 'pay-to-play'
            ],
            'regulatory': [
                'regulatory', 'regulation', 'compliance', 'oversight',
                'agency', 'commission', 'bureau'
            ],
            'political': [
                'election', 'campaign', 'vote', 'ballot', 'democracy',
                'political', 'government', 'administration'
            ],
            'financial': [
                'money', 'payment', 'funding', 'finance', 'investment',
                'cryptocurrency', 'bitcoin', 'transaction'
            ],
            'legal': [
                'court', 'judge', 'legal', 'lawsuit', 'litigation',
                'justice', 'judicial', 'attorney'
            ],
            'media': [
                'media', 'news', 'press', 'journalism', 'publication',
                'broadcast', 'social media', 'platform'
            ]
        }
    
    def chunk(self, document: str, config) -> List:
        """Chunk document by topics."""
        from .semantic_chunker import SemanticChunk
        
        # First split by sentences to get manageable units
        sentences = SentenceChunker()._split_sentences(document)
        
        if not sentences:
            return []
        
        # Assign topic scores to each sentence
        sentence_topics = self._analyze_sentence_topics(sentences)
        
        # Group sentences by dominant topics
        topic_groups = self._group_by_topics(sentences, sentence_topics, config)
        
        # Convert topic groups to chunks
        chunks = []
        for topic, group_sentences in topic_groups.items():
            if not group_sentences:
                continue
            
            chunk_text = ' '.join(group_sentences)
            word_count = len(chunk_text.split())
            
            # Skip very small chunks
            if word_count < config.min_chunk_size:
                continue
            
            chunk = SemanticChunk(
                id=f"topic_chunk_{len(chunks)}_{topic}",
                text=chunk_text,
                start_idx=0,
                end_idx=len(chunk_text),
                word_count=word_count
            )
            chunks.append(chunk)
        
        # If no topic-based chunks created, fallback to sentence chunking
        if not chunks:
            sentence_chunker = SentenceChunker()
            chunks = sentence_chunker.chunk(document, config)
        
        return chunks
    
    def _analyze_sentence_topics(self, sentences: List[str]) -> List[Dict[str, float]]:
        """Analyze topic distribution for each sentence."""
        sentence_topics = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            topic_scores = {}
            
            # Calculate topic scores based on keyword presence
            for topic, keywords in self.topic_keywords.items():
                score = 0.0
                for keyword in keywords:
                    if keyword in sentence_lower:
                        # Weight longer keywords higher
                        score += len(keyword.split())
                
                if score > 0:
                    topic_scores[topic] = score
            
            sentence_topics.append(topic_scores)
        
        return sentence_topics
    
    def _group_by_topics(self, 
                        sentences: List[str], 
                        sentence_topics: List[Dict[str, float]],
                        config) -> Dict[str, List[str]]:
        """Group sentences by dominant topics."""
        topic_groups = defaultdict(list)
        current_topic = None
        current_group = []
        current_word_count = 0
        
        for sentence, topics in zip(sentences, sentence_topics):
            sentence_words = len(sentence.split())
            
            # Determine dominant topic for sentence
            if topics:
                dominant_topic = max(topics.keys(), key=lambda k: topics[k])
            else:
                dominant_topic = 'general'
            
            # Check if we should continue current group or start new one
            if (current_topic == dominant_topic and 
                current_word_count + sentence_words <= config.target_chunk_size):
                # Continue current group
                current_group.append(sentence)
                current_word_count += sentence_words
                
            else:
                # Start new group
                if current_group and current_topic:
                    topic_groups[current_topic].extend(current_group)
                
                current_topic = dominant_topic
                current_group = [sentence]
                current_word_count = sentence_words
        
        # Add final group
        if current_group and current_topic:
            topic_groups[current_topic].extend(current_group)
        
        return dict(topic_groups)


class HierarchicalChunker(BaseChunkingStrategy):
    """
    Hierarchical chunking that creates multiple levels of chunks.
    
    Creates parent chunks for broad context and child chunks for specific
    details, enabling multi-level retrieval strategies.
    """
    
    def chunk(self, document: str, config) -> List:
        """Create hierarchical chunks."""
        from .semantic_chunker import SemanticChunk
        
        # Level 1: Large contextual chunks
        large_chunks = self._create_large_chunks(document, config)
        
        # Level 2: Standard chunks within each large chunk
        all_chunks = []
        
        for large_chunk in large_chunks:
            # Create standard-sized child chunks
            child_chunks = self._create_child_chunks(large_chunk, config)
            
            # Set parent-child relationships
            for child in child_chunks:
                child.parent_chunk_id = large_chunk.id
                large_chunk.child_chunk_ids.append(child.id)
            
            # Add both parent and children to results
            all_chunks.append(large_chunk)
            all_chunks.extend(child_chunks)
        
        return all_chunks
    
    def _create_large_chunks(self, document: str, config) -> List:
        """Create large contextual chunks."""
        from .semantic_chunker import SemanticChunk
        
        # Use paragraph chunker with larger target size
        large_config = type(config)(
            target_chunk_size=config.target_chunk_size * 3,
            min_chunk_size=config.min_chunk_size * 2,
            max_chunk_size=config.max_chunk_size * 2
        )
        
        paragraph_chunker = ParagraphChunker()
        large_chunks = paragraph_chunker.chunk(document, large_config)
        
        # Update IDs to indicate hierarchy level
        for i, chunk in enumerate(large_chunks):
            chunk.id = f"L1_chunk_{i}"
        
        return large_chunks
    
    def _create_child_chunks(self, parent_chunk, config) -> List:
        """Create child chunks within a parent chunk."""
        # Use sentence chunker for child chunks
        sentence_chunker = SentenceChunker()
        child_chunks = sentence_chunker.chunk(parent_chunk.text, config)
        
        # Update IDs to indicate hierarchy and parent relationship
        for i, chunk in enumerate(child_chunks):
            chunk.id = f"L2_{parent_chunk.id}_child_{i}"
        
        return child_chunks
    
    def _should_split_chunk(self, chunk, config) -> bool:
        """Determine if a chunk should be split into smaller pieces."""
        # Split if chunk is too large or has low coherence
        return (chunk.word_count > config.target_chunk_size * 1.5 or
                chunk.coherence_score < config.min_semantic_coherence)
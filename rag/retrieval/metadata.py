"""
Metadata-Based Retrieval Component

Smart metadata filtering and retrieval using extracted filters
from natural language queries.
"""

import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import re
from collections import defaultdict

logger = logging.getLogger(__name__)


class MetadataRetriever:
    """
    Metadata-based retrieval using smart filtering.
    
    Retrieves events based on:
    - Extracted date filters (years, months, relative time)
    - Actor filters (political figures, organizations)
    - Importance filters (critical, major, etc.)
    - Tag filters (topic-based filtering)
    - Combined filter logic with fallbacks
    """
    
    def __init__(self, collection):
        """
        Initialize metadata retriever.
        
        Args:
            collection: ChromaDB collection
        """
        self.collection = collection
        self.retrieval_count = 0
        
        # Cache for common filter patterns
        self._filter_cache = {}
    
    def retrieve_with_filters(self, filters: Dict[str, Any], n_results: int = 30) -> List[Dict]:
        """
        Retrieve events using metadata filters.
        
        Args:
            filters: Dictionary of extracted filters
            n_results: Maximum number of results
            
        Returns:
            List of filtered results with metadata scores
        """
        self.retrieval_count += 1
        
        if not filters:
            logger.debug("No filters provided, returning empty results")
            return []
        
        try:
            # Build ChromaDB where clause from filters
            where_clause = self._build_where_clause(filters)
            
            if not where_clause:
                logger.debug("No valid where clause built from filters")
                return []
            
            logger.debug(f"Metadata query with where clause: {where_clause}")
            
            # Query with metadata filters
            results = self.collection.query(
                query_texts=[""],  # Empty query for metadata-only search
                n_results=n_results,
                where=where_clause,
                include=['metadatas', 'documents']
            )
            
            # Process and score results
            scored_results = self._score_metadata_results(results, filters)
            
            logger.debug(f"Metadata retrieval: {len(scored_results)} results")
            return scored_results
            
        except Exception as e:
            logger.error(f"Metadata retrieval failed: {e}")
            return []
    
    def _build_where_clause(self, filters: Dict[str, Any]) -> Optional[Dict]:
        """
        Build ChromaDB where clause from extracted filters.
        
        Args:
            filters: Extracted filters dictionary
            
        Returns:
            ChromaDB where clause or None if no valid filters
        """
        conditions = []
        
        # Date filters
        date_conditions = self._build_date_conditions(filters.get('date_filters', {}))
        if date_conditions:
            conditions.extend(date_conditions)
        
        # Actor filters
        actor_conditions = self._build_actor_conditions(filters.get('actor_filters', []))
        if actor_conditions:
            conditions.extend(actor_conditions)
        
        # Importance filters
        importance_conditions = self._build_importance_conditions(filters.get('importance_filters', []))
        if importance_conditions:
            conditions.extend(importance_conditions)
        
        # Tag filters
        tag_conditions = self._build_tag_conditions(filters.get('tag_filters', []))
        if tag_conditions:
            conditions.extend(tag_conditions)
        
        # Status filters
        status_conditions = self._build_status_conditions(filters.get('status_filters', []))
        if status_conditions:
            conditions.extend(status_conditions)
        
        # Combine conditions
        if not conditions:
            return None
        elif len(conditions) == 1:
            return conditions[0]
        else:
            # Use AND logic for multiple filter types
            return {"$and": conditions}
    
    def _build_date_conditions(self, date_filters: Dict) -> List[Dict]:
        """Build date-based where conditions."""
        conditions = []
        
        # Year filters
        if 'years' in date_filters and date_filters['years']:
            years = date_filters['years']
            if len(years) == 1:
                # Single year - look for year string in date field
                conditions.append({
                    "date": {"$regex": f".*{years[0]}.*"}
                })
            else:
                # Multiple years - OR condition
                year_conditions = [
                    {"date": {"$regex": f".*{year}.*"}} for year in years
                ]
                conditions.append({"$or": year_conditions})
        
        # Month filters (combined with years if available)
        if 'months' in date_filters and date_filters['months']:
            month_patterns = []
            for month in date_filters['months']:
                # Handle different month formats
                if isinstance(month, int):
                    month_patterns.append(f"{month:02d}")
                elif isinstance(month, str):
                    month_patterns.append(month.lower())
            
            if month_patterns:
                month_conditions = [
                    {"date": {"$regex": f".*{pattern}.*"}} for pattern in month_patterns
                ]
                conditions.append({"$or": month_conditions})
        
        # Relative time filters
        if 'relative_time' in date_filters:
            relative = date_filters['relative_time']
            current_year = datetime.now().year
            
            if 'recent' in relative or 'current' in relative:
                # Recent: last 2 years
                recent_years = [str(current_year), str(current_year - 1)]
                recent_conditions = [
                    {"date": {"$regex": f".*{year}.*"}} for year in recent_years
                ]
                conditions.append({"$or": recent_conditions})
            
            elif 'last year' in relative:
                conditions.append({
                    "date": {"$regex": f".*{current_year - 1}.*"}
                })
        
        return conditions
    
    def _build_actor_conditions(self, actor_filters: List[str]) -> List[Dict]:
        """Build actor-based where conditions."""
        if not actor_filters:
            return []
        
        conditions = []
        
        # Group similar actors (case-insensitive partial matching)
        grouped_actors = self._group_similar_actors(actor_filters)
        
        for actor_group in grouped_actors:
            # Create OR conditions for each actor group
            actor_conditions = []
            
            for actor in actor_group:
                # Search in actors field (handle both string and array)
                actor_conditions.append({
                    "actors": {"$regex": f".*{re.escape(actor)}.*", "$options": "i"}
                })
            
            if len(actor_conditions) == 1:
                conditions.append(actor_conditions[0])
            else:
                conditions.append({"$or": actor_conditions})
        
        return conditions
    
    def _group_similar_actors(self, actor_filters: List[str]) -> List[List[str]]:
        """Group similar actor names together."""
        if not actor_filters:
            return []
        
        groups = []
        used = set()
        
        for actor in actor_filters:
            if actor in used:
                continue
            
            # Find similar actors (same last name, initials, etc.)
            similar_group = [actor]
            used.add(actor)
            
            for other_actor in actor_filters:
                if other_actor in used:
                    continue
                
                if self._actors_are_similar(actor, other_actor):
                    similar_group.append(other_actor)
                    used.add(other_actor)
            
            groups.append(similar_group)
        
        return groups
    
    def _actors_are_similar(self, actor1: str, actor2: str) -> bool:
        """Check if two actor names likely refer to the same person."""
        a1_words = actor1.lower().split()
        a2_words = actor2.lower().split()
        
        # Same last name
        if a1_words[-1] == a2_words[-1] and len(a1_words) > 1 and len(a2_words) > 1:
            return True
        
        # One is initials + last name of the other
        if len(a1_words) == 2 and len(a2_words) >= 2:
            if (a1_words[0][0] == a2_words[0][0] and 
                a1_words[1] == a2_words[-1]):
                return True
        
        return False
    
    def _build_importance_conditions(self, importance_filters: List[str]) -> List[Dict]:
        """Build importance-based where conditions."""
        if not importance_filters:
            return []
        
        # Map importance terms to broader categories
        importance_mapping = {
            'critical': ['critical', 'crucial', 'vital'],
            'major': ['major', 'significant', 'important'],
            'high': ['high', 'elevated', 'priority'],
            'breaking': ['breaking', 'urgent', 'emergency']
        }
        
        conditions = []
        
        for imp_filter in importance_filters:
            imp_lower = imp_filter.lower()
            
            # Find matching importance category
            matched_terms = [imp_lower]
            for category, terms in importance_mapping.items():
                if imp_lower in terms:
                    matched_terms = terms
                    break
            
            # Create OR condition for all matched terms
            imp_conditions = [
                {"importance": {"$regex": f".*{term}.*", "$options": "i"}}
                for term in matched_terms
            ]
            
            if len(imp_conditions) == 1:
                conditions.append(imp_conditions[0])
            else:
                conditions.append({"$or": imp_conditions})
        
        return conditions
    
    def _build_tag_conditions(self, tag_filters: List[str]) -> List[Dict]:
        """Build tag-based where conditions."""
        if not tag_filters:
            return []
        
        conditions = []
        
        for tag in tag_filters:
            # Search in tags field (handle both string and array)
            conditions.append({
                "tags": {"$regex": f".*{re.escape(tag)}.*", "$options": "i"}
            })
        
        # Use OR logic for tags (match any tag)
        if len(conditions) == 1:
            return conditions
        else:
            return [{"$or": conditions}]
    
    def _build_status_conditions(self, status_filters: List[str]) -> List[Dict]:
        """Build status-based where conditions."""
        if not status_filters:
            return []
        
        conditions = []
        
        for status in status_filters:
            conditions.append({
                "status": {"$regex": f".*{re.escape(status)}.*", "$options": "i"}
            })
        
        # Use OR logic for status filters
        if len(conditions) == 1:
            return conditions
        else:
            return [{"$or": conditions}]
    
    def _score_metadata_results(self, results: Dict, filters: Dict[str, Any]) -> List[Dict]:
        """
        Score metadata results based on filter match quality.
        
        Args:
            results: Raw ChromaDB results
            filters: Original filters for scoring
            
        Returns:
            List of scored results
        """
        if not results['ids'] or not results['ids'][0]:
            return []
        
        scored_results = []
        
        for i in range(len(results['ids'][0])):
            event_id = results['ids'][0][i]
            metadata = results['metadatas'][0][i]
            document = results['documents'][0][i]
            
            # Calculate metadata match score
            metadata_score = self._calculate_metadata_score(metadata, filters)
            
            result = {
                'id': event_id,
                'metadata': metadata,
                'document': document,
                'metadata_score': metadata_score
            }
            
            scored_results.append(result)
        
        # Sort by metadata score
        scored_results.sort(key=lambda x: x['metadata_score'], reverse=True)
        
        return scored_results
    
    def _calculate_metadata_score(self, metadata: Dict, filters: Dict[str, Any]) -> float:
        """
        Calculate how well metadata matches the filters.
        
        Args:
            metadata: Event metadata
            filters: Original filters
            
        Returns:
            Metadata match score (0-1)
        """
        total_score = 0.0
        max_possible_score = 0.0
        
        # Date match scoring
        if 'date_filters' in filters:
            date_score, date_max = self._score_date_match(metadata.get('date', ''), filters['date_filters'])
            total_score += date_score
            max_possible_score += date_max
        
        # Actor match scoring
        if 'actor_filters' in filters:
            actor_score, actor_max = self._score_actor_match(metadata.get('actors', []), filters['actor_filters'])
            total_score += actor_score
            max_possible_score += actor_max
        
        # Importance match scoring
        if 'importance_filters' in filters:
            imp_score, imp_max = self._score_importance_match(metadata.get('importance', ''), filters['importance_filters'])
            total_score += imp_score
            max_possible_score += imp_max
        
        # Tag match scoring
        if 'tag_filters' in filters:
            tag_score, tag_max = self._score_tag_match(metadata.get('tags', []), filters['tag_filters'])
            total_score += tag_score
            max_possible_score += tag_max
        
        # Normalize score
        if max_possible_score > 0:
            return min(1.0, total_score / max_possible_score)
        else:
            return 0.8  # Default score for metadata matches
    
    def _score_date_match(self, event_date: str, date_filters: Dict) -> tuple:
        """Score date match quality."""
        score = 0.0
        max_score = 3.0  # Maximum possible date score
        
        if not event_date:
            return score, max_score
        
        # Year match
        if 'years' in date_filters:
            for year in date_filters['years']:
                if str(year) in event_date:
                    score += 2.0
                    break
        
        # Month match
        if 'months' in date_filters:
            for month in date_filters['months']:
                month_str = str(month).lower()
                if month_str in event_date.lower():
                    score += 1.0
                    break
        
        return score, max_score
    
    def _score_actor_match(self, event_actors: Any, actor_filters: List[str]) -> tuple:
        """Score actor match quality."""
        score = 0.0
        max_score = len(actor_filters) * 2.0
        
        if isinstance(event_actors, str):
            event_actors = [event_actors]
        elif not isinstance(event_actors, list):
            event_actors = []
        
        for actor_filter in actor_filters:
            for event_actor in event_actors:
                if isinstance(event_actor, str):
                    if actor_filter.lower() in event_actor.lower():
                        score += 2.0
                        break
                    elif any(word in event_actor.lower() for word in actor_filter.lower().split()):
                        score += 1.0
                        break
        
        return score, max_score
    
    def _score_importance_match(self, event_importance: str, importance_filters: List[str]) -> tuple:
        """Score importance match quality."""
        score = 0.0
        max_score = 2.0
        
        if not event_importance:
            return score, max_score
        
        importance_lower = event_importance.lower()
        
        for imp_filter in importance_filters:
            if imp_filter.lower() in importance_lower:
                score += 2.0
                break
            elif any(word in importance_lower for word in imp_filter.lower().split()):
                score += 1.0
                break
        
        return score, max_score
    
    def _score_tag_match(self, event_tags: Any, tag_filters: List[str]) -> tuple:
        """Score tag match quality."""
        score = 0.0
        max_score = len(tag_filters) * 1.5
        
        if isinstance(event_tags, str):
            event_tags = [event_tags]
        elif not isinstance(event_tags, list):
            event_tags = []
        
        for tag_filter in tag_filters:
            for event_tag in event_tags:
                if isinstance(event_tag, str):
                    if tag_filter.lower() in event_tag.lower():
                        score += 1.5
                        break
                    elif any(word in event_tag.lower() for word in tag_filter.lower().split()):
                        score += 0.75
                        break
        
        return score, max_score
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retrieval statistics."""
        return {
            'retrieval_count': self.retrieval_count,
            'cache_size': len(self._filter_cache)
        }
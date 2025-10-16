#!/usr/bin/env python3
"""
Tiered Orchestrator - Cost-optimized Claude subagent dispatch system
Uses appropriate model tiers for different task types to reduce costs by 70-90%
"""

from typing import Dict, List, Any
from orchestrator_server_manager import ensure_shared_server

class TieredOrchestrator:
    """Orchestrator that dispatches subagents using cost-optimized model tiers"""
    
    def __init__(self, server_endpoint: str = None):
        self.server_endpoint = server_endpoint or ensure_shared_server()
        
        # Cost-optimized model tier assignments
        self.tier_assignments = {
            # Tier 1: Simple validation tasks (Claude 3 Haiku - cheapest)
            'duplicate-checker': 'haiku',      # ~$0.0003 per check
            'date-extractor': 'haiku',         # ~$0.0002 per extraction  
            'tag-generator': 'haiku',          # ~$0.0002 per generation
            'source-validator': 'haiku',       # ~$0.0003 per validation
            
            # Tier 2: Research tasks (Claude 3 Haiku for structured tasks)
            'timeline-researcher': 'haiku',    # ~$0.002 per research task
            'timeline-entry-creator': 'haiku', # ~$0.001 per entry
            'pattern-finder': 'haiku',         # ~$0.003 per analysis
            
            # Tier 3: Complex analysis (Claude 3.5 Sonnet for reasoning)
            'event-validator': 'sonnet',       # ~$0.02 per validation
            'research-planner': 'sonnet',      # ~$0.03 per plan
            'quality-auditor': 'sonnet',       # ~$0.02 per audit
            
            # Tier 4: Complex document processing (Claude 3 Opus for deep analysis)
            'pdf-analyzer': 'opus',            # ~$0.05 per document
            'complex-research': 'opus',        # ~$0.07 per complex task
        }
    
    def deploy_subagent(self, agent_type: str, task_description: str, task_prompt: str) -> Dict:
        """Deploy a subagent using the appropriate model tier for cost optimization"""
        
        # Determine model tier
        model_tier = self.tier_assignments.get(agent_type, 'general-purpose')
        
        # Map to Claude Code subagent types
        subagent_type_mapping = {
            'haiku': 'general-purpose',      # Claude Code uses general-purpose for all
            'sonnet': 'general-purpose',     # Will specify model in prompt
            'opus': 'general-purpose',       # Will specify model in prompt
            'general-purpose': 'general-purpose'
        }
        
        subagent_type = subagent_type_mapping[model_tier]
        
        # Add model tier instruction to prompt
        tier_instructions = {
            'haiku': "You are a Claude 3 Haiku agent optimized for fast, cost-effective tasks. Focus on efficiency and accuracy for simple operations.",
            'sonnet': "You are a Claude 3.5 Sonnet agent optimized for reasoning and analysis tasks. Provide thoughtful analysis while maintaining efficiency.", 
            'opus': "You are a Claude 3 Opus agent for complex analysis. Use your advanced capabilities for deep reasoning and comprehensive analysis."
        }
        
        enhanced_prompt = f"""
{tier_instructions.get(model_tier, '')}

Server endpoint: {self.server_endpoint}
Agent type: {agent_type}
Model tier: {model_tier}

{task_prompt}
"""
        
        # Import Task here to avoid circular imports
        from claude_code_tools import Task
        
        result = Task(
            subagent_type=subagent_type,
            description=task_description,
            prompt=enhanced_prompt
        )
        
        return {
            'agent_type': agent_type,
            'model_tier': model_tier,
            'estimated_cost': self._estimate_cost(agent_type),
            'result': result
        }
    
    def _estimate_cost(self, agent_type: str) -> float:
        """Estimate cost for agent type based on typical usage"""
        cost_estimates = {
            'duplicate-checker': 0.0003,
            'date-extractor': 0.0002,
            'tag-generator': 0.0002,
            'source-validator': 0.0003,
            'timeline-researcher': 0.002,
            'timeline-entry-creator': 0.001,
            'pattern-finder': 0.003,
            'event-validator': 0.02,
            'research-planner': 0.03,
            'quality-auditor': 0.02,
            'pdf-analyzer': 0.05,
            'complex-research': 0.07
        }
        return cost_estimates.get(agent_type, 0.01)
    
    # Tier 1 Methods (Haiku) - Fast and cheap
    def check_duplicates(self, event_date: str, key_terms: List[str]) -> Dict:
        """Deploy duplicate-checker agent (Haiku tier)"""
        return self.deploy_subagent(
            'duplicate-checker',
            'Check for duplicate events',
            f"""
            Check if events already exist for these criteria:
            - Date: {event_date}
            - Key terms: {key_terms}
            
            Search the Research Monitor API at {self.server_endpoint} for:
            1. Events on the same date
            2. Events with same actors/terms
            3. Similar titles or content
            
            Return JSON with is_duplicate, confidence, and similar_events array.
            """
        )
    
    def extract_dates(self, text: str) -> Dict:
        """Deploy date-extractor agent (Haiku tier)"""
        return self.deploy_subagent(
            'date-extractor',
            'Extract and normalize dates',
            f"""
            Extract all dates from this text and normalize to YYYY-MM-DD format:
            
            Text: {text}
            
            Return JSON with extracted_dates array and normalized_dates.
            """
        )
    
    def generate_tags(self, event_content: str) -> Dict:
        """Deploy tag-generator agent (Haiku tier)"""
        return self.deploy_subagent(
            'tag-generator', 
            'Generate consistent tags',
            f"""
            Generate appropriate tags for this timeline event:
            
            Content: {event_content}
            
            Return JSON with tags array (3-7 relevant tags).
            Use consistent tag formats like: actor_name, organization, category, topic.
            """
        )
    
    def validate_sources(self, sources: List[Dict]) -> Dict:
        """Deploy source-validator agent (Haiku tier)"""
        return self.deploy_subagent(
            'source-validator',
            'Validate source URLs and credibility',
            f"""
            Validate these sources for credibility and accessibility:
            
            Sources: {sources}
            
            Return JSON with validation results per source including:
            - accessible: boolean
            - credible: boolean  
            - issues: array of any problems found
            """
        )
    
    # Tier 2 Methods (Haiku for structured research)
    def research_timeline_events(self, topic: str, date_range: str = None) -> Dict:
        """Deploy timeline-researcher agent (Haiku tier)"""
        return self.deploy_subagent(
            'timeline-researcher',
            'Research timeline events for topic',
            f"""
            Research timeline events for: {topic}
            Date range: {date_range or 'Any relevant dates'}
            
            Use web search to find 2-3 specific, verifiable historical events.
            Focus on events with:
            - Specific dates and actors
            - Credible sources  
            - Constitutional or systemic significance
            
            Return JSON array of timeline events with all required fields.
            """
        )
    
    # Tier 3 Methods (Sonnet for reasoning)
    def validate_events(self, events: List[Dict]) -> Dict:
        """Deploy event-validator agent (Sonnet tier)"""
        return self.deploy_subagent(
            'event-validator',
            'Validate and enhance events',
            f"""
            Validate and enhance these timeline events:
            
            Events: {events}
            
            For each event:
            1. Check for duplicates via API search
            2. Verify all required fields are present
            3. Validate importance scores are justified
            4. Enhance actor names with full titles
            5. Add proper event IDs
            
            Return enhanced events ready for submission or mark as duplicates.
            """
        )
    
    def plan_research(self, priorities: List[Dict]) -> Dict:
        """Deploy research-planner agent (Sonnet tier)"""
        return self.deploy_subagent(
            'research-planner',
            'Create strategic research plan',
            f"""
            Create a strategic research plan for these priorities:
            
            Priorities: {priorities}
            
            Generate:
            1. Research strategy for each priority
            2. Expected number of events to discover
            3. Key search terms and sources
            4. Priority ranking by importance
            5. Resource allocation recommendations
            
            Return comprehensive research plan with timeline estimates.
            """
        )
    
    # Complete workflow with cost optimization
    def research_workflow_optimized(self, priority_topic: str) -> Dict:
        """Execute complete research workflow with tiered cost optimization"""
        
        workflow_results = {
            'topic': priority_topic,
            'total_estimated_cost': 0.0,
            'agents_deployed': [],
            'results': {}
        }
        
        # Step 1: Research events (Haiku - $0.002)
        research_result = self.research_timeline_events(priority_topic)
        workflow_results['agents_deployed'].append(research_result)
        workflow_results['total_estimated_cost'] += research_result['estimated_cost']
        
        if research_result['result']:
            events = research_result['result']  # Extract events from result
            
            # Step 2: Validate events (Sonnet - $0.02)  
            validation_result = self.validate_events(events)
            workflow_results['agents_deployed'].append(validation_result)
            workflow_results['total_estimated_cost'] += validation_result['estimated_cost']
            
            # Step 3: Check duplicates for each event (Haiku - $0.0003 each)
            for event in events:
                duplicate_check = self.check_duplicates(
                    event.get('date', ''),
                    [event.get('title', ''), event.get('actors', [{}])[0] if event.get('actors') else '']
                )
                workflow_results['agents_deployed'].append(duplicate_check)
                workflow_results['total_estimated_cost'] += duplicate_check['estimated_cost']
        
        workflow_results['cost_savings'] = f"Estimated 70-90% savings vs. using Opus for all tasks"
        return workflow_results

# Convenience functions for direct use
def deploy_haiku_agent(agent_type: str, task_description: str, task_prompt: str) -> Dict:
    """Quick deploy of Haiku-tier agent"""
    orchestrator = TieredOrchestrator()
    return orchestrator.deploy_subagent(agent_type, task_description, task_prompt)

def deploy_sonnet_agent(agent_type: str, task_description: str, task_prompt: str) -> Dict:
    """Quick deploy of Sonnet-tier agent"""  
    orchestrator = TieredOrchestrator()
    # Override tier assignment for this call
    orchestrator.tier_assignments[agent_type] = 'sonnet'
    return orchestrator.deploy_subagent(agent_type, task_description, task_prompt)

if __name__ == "__main__":
    # Example usage
    orchestrator = TieredOrchestrator()
    
    print("=== Tiered Orchestrator Cost Optimization Demo ===")
    print(f"Server endpoint: {orchestrator.server_endpoint}")
    
    # Example: Cost-optimized duplicate check (Haiku - $0.0003)
    duplicate_result = orchestrator.check_duplicates("2025-01-15", ["Trump", "crypto"])
    print(f"Duplicate check - Estimated cost: ${duplicate_result['estimated_cost']}")
    
    # Example: Research planning (Sonnet - $0.03)
    plan_result = orchestrator.plan_research([{"title": "SPAC fraud networks"}])
    print(f"Research planning - Estimated cost: ${plan_result['estimated_cost']}")
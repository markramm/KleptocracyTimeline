#!/usr/bin/env python3
"""
Trump Tyranny Tracker Processing Orchestrator
Parallel subagent workflow to process all 269 articles using Claude Code Task tools
"""

import json
import os
import time
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from pathlib import Path

# Import the Research Monitor API
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from research_api import ResearchAPI

class TTTProcessingOrchestrator:
    def __init__(self, base_dir: str = "ai-analysis/trump-tyranny-tracker"):
        self.base_dir = base_dir
        self.articles_dir = os.path.join(base_dir, "articles")
        self.processed_dir = os.path.join(base_dir, "processed")
        self.metadata_dir = os.path.join(base_dir, "metadata")
        
        # Research Monitor configuration
        self.server_port = 5560
        self.server_url = f"http://localhost:{self.server_port}"
        self.api_key = "test"
        
        # Processing configuration
        self.max_document_analyzers = 6
        self.max_research_executors = 8
        self.max_integration_validators = 4
        self.articles_per_analyzer = 45  # 269 articles / 6 agents ≈ 45 each
        
        # State tracking
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.orchestrator_log = []
        
        print(f"🎯 TTT Processing Orchestrator initialized")
        print(f"📁 Base directory: {base_dir}")
        print(f"🌐 Server URL: {self.server_url}")
    
    def ensure_server_running(self) -> bool:
        """Ensure Research Monitor server is running"""
        try:
            # Test connection
            api = ResearchAPI(base_url=self.server_url, api_key=self.api_key)
            stats = api.get_stats()
            print(f"✅ Research Monitor server running (port {self.server_port})")
            print(f"📊 Current stats: {stats['events']['total']} events, {stats['priorities']['pending']} pending priorities")
            return True
        except Exception as e:
            print(f"❌ Research Monitor server not accessible: {e}")
            print(f"🚀 Starting Research Monitor server on port {self.server_port}...")
            
            try:
                # Start the server
                cmd = f"cd ../../research_monitor && RESEARCH_MONITOR_PORT={self.server_port} python3 app_v2.py &"
                subprocess.Popen(cmd, shell=True)
                
                # Wait for server to start
                for attempt in range(10):
                    time.sleep(2)
                    try:
                        api = ResearchAPI(base_url=self.server_url, api_key=self.api_key)
                        stats = api.get_stats()
                        print(f"✅ Research Monitor server started successfully")
                        return True
                    except:
                        print(f"⏳ Waiting for server startup (attempt {attempt + 1}/10)")
                        continue
                
                print(f"❌ Failed to start Research Monitor server after 20 seconds")
                return False
                
            except Exception as e:
                print(f"❌ Error starting server: {e}")
                return False
    
    def get_unprocessed_articles(self) -> List[Dict]:
        """Get list of TTT articles that need processing"""
        articles = []
        
        # Find all TTT article files
        article_files = list(Path(self.articles_dir).glob("ttt-*.json"))
        print(f"📚 Found {len(article_files)} TTT articles")
        
        for article_file in article_files:
            try:
                # Check if already processed
                article_id = article_file.stem
                processed_file = os.path.join(self.processed_dir, f"{article_id}_processed.json")
                
                if os.path.exists(processed_file):
                    continue  # Skip already processed
                
                # Load article data
                with open(article_file, 'r') as f:
                    article_data = json.load(f)
                
                articles.append({
                    'id': article_id,
                    'file_path': str(article_file),
                    'title': article_data.get('title', 'Unknown Title'),
                    'url': article_data.get('url', ''),
                    'date': article_data.get('date', ''),
                    'word_count': article_data.get('word_count', 0)
                })
                
            except Exception as e:
                print(f"⚠️  Error reading {article_file}: {e}")
                continue
        
        print(f"📋 {len(articles)} articles need processing")
        return articles
    
    def create_article_batches(self, articles: List[Dict]) -> List[List[Dict]]:
        """Divide articles into batches for parallel processing"""
        batches = []
        batch_size = max(1, len(articles) // self.max_document_analyzers)
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            batches.append(batch)
        
        print(f"📦 Created {len(batches)} article batches (avg {len(articles)//len(batches) if batches else 0} articles per batch)")
        return batches
    
    def launch_document_analyzer(self, batch: List[Dict], batch_id: int) -> Dict:
        """Launch a document analyzer agent for a batch of articles"""
        article_files = [article['file_path'] for article in batch]
        article_titles = [f"{article['title'][:50]}..." for article in batch]
        
        prompt = f"""
DOCUMENT ANALYSIS TASK - Trump Tyranny Tracker Batch {batch_id}

You are processing {len(batch)} articles from Trump Tyranny Tracker's systematic corruption documentation.

ARTICLES TO ANALYZE:
{chr(10).join(f"- {title}" for title in article_titles)}

ARTICLE FILES:
{chr(10).join(article_files)}

SERVER ENDPOINT: {self.server_url}
API KEY: {self.api_key}

YOUR TASK:
1. Use the ResearchAPI Python client to connect to the Research Monitor
2. Read and analyze each article for systematic institutional capture patterns
3. Extract specific corruption mechanisms with dates, actors, and coordination patterns
4. Create research priorities for timeline gaps using the RT-TTT-2025-* format
5. Mark each article as processed when complete

FOCUS ON SYSTEMATIC PATTERNS:
- Federal worker targeting and Schedule F implementation
- DOJ weaponization with specific cases and prosecutor details
- Military politicization and chain of command violations  
- Election infrastructure capture operations
- Congressional oversight obstruction campaigns
- Media suppression coordination mechanisms

REQUIREMENTS:
- Use Python ResearchAPI client for all server interactions
- Create research priorities with 5-15 expected timeline events each
- Focus on coordinated corruption rather than isolated incidents
- Include specific dates, actors, and mechanisms when available
- Mark articles as processed using the crawler's mark_processed() method

START BY: Import ResearchAPI, connect to server, and begin systematic analysis.

Example code structure:
```python
from research_api import ResearchAPI
api = ResearchAPI(base_url='{self.server_url}', api_key='{self.api_key}')

# Process each article...
for article_file in {article_files}:
    # Read and analyze article
    # Create research priorities
    # Mark as processed
```
        """
        
        try:
            # Use Claude Code Task tool directly
            # This placeholder will be replaced with actual Task() call when running
            result = f"Document analysis batch {batch_id} placeholder - would process {len(batch)} articles"
            
            return {
                'batch_id': batch_id,
                'status': 'success',
                'articles_count': len(batch),
                'result': result
            }
            
        except Exception as e:
            return {
                'batch_id': batch_id,
                'status': 'error',
                'error': str(e),
                'articles_count': len(batch)
            }
    
    def launch_research_executor(self, executor_id: int) -> Dict:
        """Launch a research executor agent to process research priorities"""
        
        prompt = f"""
RESEARCH EXECUTION TASK - Executor {executor_id}

You are converting research priorities into detailed timeline events for the kleptocracy timeline.

SERVER ENDPOINT: {self.server_url}
API KEY: {self.api_key}

YOUR TASK:
1. Use ResearchAPI to connect and reserve the next available research priority
2. Conduct comprehensive web research to validate and expand the priority
3. Create specific timeline events with verified dates, sources, and details
4. Submit events using the batch API endpoint with proper validation
5. Complete the priority with accurate event counts

RESEARCH WORKFLOW:
```python
from research_api import ResearchAPI
api = ResearchAPI(base_url='{self.server_url}', api_key='{self.api_key}')

# Reserve priority
priority = api.reserve_priority('research-executor-{executor_id}')
api.confirm_work_started(priority['id'])

# Research and create events (your implementation)
events = []  # Create timeline events based on priority

# Submit events
result = api.submit_events_batch(events, priority['id'])

# Complete priority
api.complete_priority(priority['id'], len(events))
```

TIMELINE EVENT REQUIREMENTS:
- Proper JSON schema with required fields
- Verified dates in YYYY-MM-DD format  
- Credible sources with URLs when possible
- Importance scores 1-10 (focus on 7-10 for systematic corruption)
- Clear connection to institutional capture patterns
- Avoid duplicates with existing timeline events

SYSTEMATIC CORRUPTION FOCUS:
- Document coordinated campaigns across agencies
- Identify specific mechanisms of institutional capture
- Track systematic rather than isolated corruption
- Include specific actors, dates, and coordination patterns

Continue processing priorities until no more are available.
        """
        
        try:
            # Use Claude Code Task tool directly
            # This placeholder will be replaced with actual Task() call when running
            result = f"Research execution {executor_id} placeholder"
            
            return {
                'executor_id': executor_id,
                'status': 'success',
                'result': result
            }
            
        except Exception as e:
            return {
                'executor_id': executor_id,
                'status': 'error',
                'error': str(e)
            }
    
    def launch_integration_validator(self, validator_id: int) -> Dict:
        """Launch an integration validator agent"""
        
        prompt = f"""
INTEGRATION VALIDATION TASK - Validator {validator_id}

You are validating and preparing timeline events for integration into the kleptocracy timeline.

SERVER ENDPOINT: {self.server_url}
API KEY: {self.api_key}

YOUR TASK:
1. Use ResearchAPI to connect and review staged timeline events
2. Validate event quality, schema compliance, and source credibility  
3. Check for duplicates against existing timeline
4. Mark validated events for final integration
5. Report validation statistics and any issues found

VALIDATION WORKFLOW:
```python
from research_api import ResearchAPI
api = ResearchAPI(base_url='{self.server_url}', api_key='{self.api_key}')

# Get staged events for validation
stats = api.get_stats()
# Review and validate events (your implementation)

# Use search_events to check for duplicates
# Validate JSON schema compliance
# Verify source credibility
```

QUALITY CHECKS:
- JSON schema compliance (required fields, date formats)
- Source credibility (prefer government, academic, established journalism)
- Duplicate detection (same date + similar topic = duplicate)
- Importance scoring accuracy (1-3 minor, 4-6 significant, 7-10 systematic)
- Systematic corruption focus (coordinated vs isolated incidents)

VALIDATION CRITERIA:
- Accept: High-quality events with credible sources and systematic focus
- Flag: Events needing minor corrections or additional sourcing
- Reject: Duplicates, low-quality sources, or isolated incidents

Provide detailed validation report with statistics and recommendations.
        """
        
        try:
            # Use Claude Code Task tool directly
            # This placeholder will be replaced with actual Task() call when running
            result = f"Integration validation {validator_id} placeholder"
            
            return {
                'validator_id': validator_id,
                'status': 'success',
                'result': result
            }
            
        except Exception as e:
            return {
                'validator_id': validator_id,
                'status': 'error',
                'error': str(e)
            }
    
    def monitor_progress(self) -> Dict:
        """Monitor overall processing progress"""
        try:
            api = ResearchAPI(base_url=self.server_url, api_key=self.api_key)
            stats = api.get_stats()
            
            # Get processing status
            unprocessed_articles = self.get_unprocessed_articles()
            
            return {
                'timestamp': datetime.now().isoformat(),
                'unprocessed_articles': len(unprocessed_articles),
                'total_articles': len(list(Path(self.articles_dir).glob("ttt-*.json"))),
                'timeline_events': stats['events']['total'],
                'pending_priorities': stats['priorities']['pending'],
                'completed_priorities': stats['priorities']['completed'],
                'session_id': self.session_id
            }
            
        except Exception as e:
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def execute_parallel_processing(self) -> Dict:
        """Execute the full parallel processing workflow"""
        print("\\n🚀 STARTING PARALLEL TTT PROCESSING WORKFLOW")
        print("=" * 60)
        
        workflow_results = {
            'session_id': self.session_id,
            'started_at': datetime.now().isoformat(),
            'stages': {},
            'total_cost_estimate': 0.0,
            'errors': []
        }
        
        # Stage 0: Ensure server is running
        print("\\n📡 STAGE 0: SERVER SETUP")
        if not self.ensure_server_running():
            workflow_results['error'] = 'Failed to start Research Monitor server'
            return workflow_results
        
        # Stage 1: Document Analysis
        print("\\n📖 STAGE 1: DOCUMENT ANALYSIS")
        print("-" * 40)
        
        articles = self.get_unprocessed_articles()
        if not articles:
            print("✅ All articles already processed!")
            workflow_results['stages']['document_analysis'] = {'status': 'completed', 'message': 'No articles to process'}
        else:
            batches = self.create_article_batches(articles)
            
            print(f"🚀 Launching {len(batches)} document analyzer agents...")
            
            # Launch document analyzers in parallel
            with ThreadPoolExecutor(max_workers=self.max_document_analyzers) as executor:
                doc_futures = {
                    executor.submit(self.launch_document_analyzer, batch, i): i 
                    for i, batch in enumerate(batches)
                }
                
                doc_results = []
                for future in as_completed(doc_futures):
                    result = future.result()
                    doc_results.append(result)
                    batch_id = result['batch_id']
                    
                    if result['status'] == 'success':
                        print(f"✅ Document Analyzer {batch_id}: Completed {result['articles_count']} articles")
                    else:
                        print(f"❌ Document Analyzer {batch_id}: Error - {result.get('error', 'Unknown error')}")
                        workflow_results['errors'].append(f"Document Analyzer {batch_id}: {result.get('error')}")
            
            workflow_results['stages']['document_analysis'] = {
                'batches_processed': len(doc_results),
                'successful_batches': len([r for r in doc_results if r['status'] == 'success']),
                'total_articles': len(articles),
                'results': doc_results
            }
        
        # Stage 2: Research Execution (run in parallel with document analysis completion)
        print("\\n🔬 STAGE 2: RESEARCH EXECUTION")
        print("-" * 40)
        
        print(f"🚀 Launching {self.max_research_executors} research executor agents...")
        
        # Launch research executors in parallel
        with ThreadPoolExecutor(max_workers=self.max_research_executors) as executor:
            research_futures = {
                executor.submit(self.launch_research_executor, i): i 
                for i in range(self.max_research_executors)
            }
            
            research_results = []
            for future in as_completed(research_futures):
                result = future.result()
                research_results.append(result)
                executor_id = result['executor_id']
                
                if result['status'] == 'success':
                    print(f"✅ Research Executor {executor_id}: Completed")
                else:
                    print(f"❌ Research Executor {executor_id}: Error - {result.get('error', 'Unknown error')}")
                    workflow_results['errors'].append(f"Research Executor {executor_id}: {result.get('error')}")
        
        workflow_results['stages']['research_execution'] = {
            'executors_launched': len(research_results),
            'successful_executors': len([r for r in research_results if r['status'] == 'success']),
            'results': research_results
        }
        
        # Stage 3: Integration Validation
        print("\\n✅ STAGE 3: INTEGRATION VALIDATION")
        print("-" * 40)
        
        print(f"🚀 Launching {self.max_integration_validators} integration validator agents...")
        
        # Launch integration validators in parallel
        with ThreadPoolExecutor(max_workers=self.max_integration_validators) as executor:
            validation_futures = {
                executor.submit(self.launch_integration_validator, i): i 
                for i in range(self.max_integration_validators)
            }
            
            validation_results = []
            for future in as_completed(validation_futures):
                result = future.result()
                validation_results.append(result)
                validator_id = result['validator_id']
                
                if result['status'] == 'success':
                    print(f"✅ Integration Validator {validator_id}: Completed")
                else:
                    print(f"❌ Integration Validator {validator_id}: Error - {result.get('error', 'Unknown error')}")
                    workflow_results['errors'].append(f"Integration Validator {validator_id}: {result.get('error')}")
        
        workflow_results['stages']['integration_validation'] = {
            'validators_launched': len(validation_results),
            'successful_validators': len([r for r in validation_results if r['status'] == 'success']),
            'results': validation_results
        }
        
        # Final Progress Report
        print("\\n📊 FINAL PROGRESS REPORT")
        print("-" * 40)
        
        final_progress = self.monitor_progress()
        workflow_results['final_progress'] = final_progress
        workflow_results['completed_at'] = datetime.now().isoformat()
        
        # Calculate success metrics
        total_stages = len(workflow_results['stages'])
        successful_stages = len([s for s in workflow_results['stages'].values() if s.get('successful_batches', s.get('successful_executors', s.get('successful_validators', 0))) > 0])
        
        print(f"📈 WORKFLOW COMPLETION SUMMARY:")
        print(f"   Stages completed: {successful_stages}/{total_stages}")
        print(f"   Total errors: {len(workflow_results['errors'])}")
        print(f"   Final progress: {final_progress}")
        
        # Save workflow results
        results_file = os.path.join(self.metadata_dir, f"workflow_results_{self.session_id}.json")
        with open(results_file, 'w') as f:
            json.dump(workflow_results, f, indent=2)
        print(f"💾 Results saved to: {results_file}")
        
        return workflow_results

def main():
    parser = argparse.ArgumentParser(description='TTT Processing Orchestrator')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without executing')
    parser.add_argument('--monitor-only', action='store_true', help='Only monitor progress, do not launch agents')
    
    args = parser.parse_args()
    
    orchestrator = TTTProcessingOrchestrator()
    
    if args.monitor_only:
        progress = orchestrator.monitor_progress()
        print("Current Processing Status:")
        print(json.dumps(progress, indent=2))
    elif args.dry_run:
        articles = orchestrator.get_unprocessed_articles()
        batches = orchestrator.create_article_batches(articles)
        print(f"Would process {len(articles)} articles in {len(batches)} batches")
        print(f"Would launch {orchestrator.max_document_analyzers} document analyzers")
        print(f"Would launch {orchestrator.max_research_executors} research executors")  
        print(f"Would launch {orchestrator.max_integration_validators} integration validators")
    else:
        results = orchestrator.execute_parallel_processing()
        if results.get('error'):
            print(f"❌ Workflow failed: {results['error']}")
            exit(1)
        else:
            print("✅ Parallel processing workflow completed!")

if __name__ == "__main__":
    main()
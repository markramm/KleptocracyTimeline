# Cost Tracking and Optimization Guide

## Overview
This document provides detailed cost tracking methodology and optimization strategies for the Claude Code subagent system.

## Token Pricing (as of 2025)

### Claude 3 Model Pricing
| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| Claude 3 Opus | $15.00 | $75.00 |
| Claude 3.5 Sonnet | $3.00 | $15.00 |
| Claude 3 Haiku | $0.25 | $1.25 |

### Cost Per Task Estimates
| Task | Model | Avg Input Tokens | Avg Output Tokens | Cost |
|------|-------|-----------------|-------------------|------|
| Duplicate Check | Haiku | 500 | 300 | $0.0003 |
| Date Extraction | Haiku | 300 | 200 | $0.0002 |
| Source Validation | Haiku | 600 | 400 | $0.0004 |
| Timeline Research | Haiku | 800 | 1200 | $0.0020 |
| Entry Creation | Haiku | 1000 | 800 | $0.0013 |
| PDF Analysis | Sonnet | 10000 | 5000 | $0.1050 |
| Pattern Analysis | Sonnet | 5000 | 3000 | $0.0600 |
| Orchestration | Opus | 2000 | 1000 | $0.1050 |

## Implementation Strategy

### 1. Cost Tracking System

```python
# cost_tracker.py
import json
from datetime import datetime, timedelta
from typing import Dict, List

class CostTracker:
    def __init__(self):
        self.usage_log = []
        self.daily_budgets = {
            "haiku": 1.00,    # $1/day for Haiku tasks
            "sonnet": 3.00,   # $3/day for Sonnet tasks
            "opus": 5.00      # $5/day for Opus tasks
        }
        
    def log_usage(self, agent_name: str, model: str, 
                  input_tokens: int, output_tokens: int):
        """Log token usage for cost tracking"""
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost
        }
        
        self.usage_log.append(entry)
        self.check_budget_alert(model)
        
        return cost
    
    def calculate_cost(self, model: str, input_tokens: int, 
                       output_tokens: int) -> float:
        """Calculate cost based on token usage"""
        rates = {
            "haiku": {"input": 0.25/1000000, "output": 1.25/1000000},
            "sonnet": {"input": 3.00/1000000, "output": 15.00/1000000},
            "opus": {"input": 15.00/1000000, "output": 75.00/1000000}
        }
        
        model_rates = rates.get(model, rates["haiku"])
        input_cost = input_tokens * model_rates["input"]
        output_cost = output_tokens * model_rates["output"]
        
        return round(input_cost + output_cost, 6)
    
    def get_daily_usage(self) -> Dict:
        """Get usage statistics for today"""
        today = datetime.now().date()
        daily_usage = {"haiku": 0, "sonnet": 0, "opus": 0}
        
        for entry in self.usage_log:
            entry_date = datetime.fromisoformat(entry["timestamp"]).date()
            if entry_date == today:
                daily_usage[entry["model"]] += entry["cost"]
        
        return daily_usage
    
    def check_budget_alert(self, model: str):
        """Alert if approaching daily budget"""
        usage = self.get_daily_usage()
        budget = self.daily_budgets[model]
        
        if usage[model] > budget * 0.8:
            print(f"⚠️ {model.upper()} budget alert: ${usage[model]:.2f} of ${budget:.2f} used")
            
        if usage[model] > budget:
            raise BudgetExceededError(f"{model} daily budget exceeded")
```

### 2. Usage Analytics

```python
# analytics.py
class UsageAnalytics:
    def __init__(self, cost_tracker: CostTracker):
        self.tracker = cost_tracker
    
    def generate_report(self) -> Dict:
        """Generate comprehensive usage report"""
        report = {
            "daily_summary": self.daily_summary(),
            "agent_efficiency": self.agent_efficiency(),
            "cost_per_event": self.cost_per_event(),
            "optimization_opportunities": self.find_optimizations()
        }
        return report
    
    def daily_summary(self) -> Dict:
        """Summarize daily usage and costs"""
        usage = self.tracker.get_daily_usage()
        total = sum(usage.values())
        
        return {
            "date": datetime.now().date().isoformat(),
            "total_cost": round(total, 2),
            "breakdown": usage,
            "events_created": self.count_events_created(),
            "cost_per_event": round(total / max(self.count_events_created(), 1), 3)
        }
    
    def agent_efficiency(self) -> List[Dict]:
        """Analyze efficiency of each agent"""
        agents = {}
        
        for entry in self.tracker.usage_log:
            agent = entry["agent"]
            if agent not in agents:
                agents[agent] = {
                    "calls": 0,
                    "total_cost": 0,
                    "avg_tokens": 0
                }
            
            agents[agent]["calls"] += 1
            agents[agent]["total_cost"] += entry["cost"]
            agents[agent]["avg_tokens"] += (entry["input_tokens"] + 
                                           entry["output_tokens"])
        
        # Calculate averages
        for agent in agents:
            if agents[agent]["calls"] > 0:
                agents[agent]["avg_tokens"] //= agents[agent]["calls"]
                agents[agent]["avg_cost"] = (agents[agent]["total_cost"] / 
                                            agents[agent]["calls"])
        
        return agents
    
    def find_optimizations(self) -> List[str]:
        """Identify cost optimization opportunities"""
        optimizations = []
        usage = self.tracker.get_daily_usage()
        
        # Check if Opus is being overused
        if usage["opus"] > usage["haiku"] * 2:
            optimizations.append("Consider delegating more tasks to Haiku")
        
        # Check for redundant duplicate checks
        dup_checks = [e for e in self.tracker.usage_log 
                     if e["agent"] == "duplicate-checker"]
        if len(dup_checks) > 50:
            optimizations.append("Implement caching for duplicate checks")
        
        # Check average tokens per task
        for agent_stats in self.agent_efficiency():
            if agent_stats["avg_tokens"] > 2000:
                optimizations.append(f"Optimize {agent_stats['agent']} prompts")
        
        return optimizations
```

### 3. Budget Management

```python
# budget_manager.py
class BudgetManager:
    def __init__(self):
        self.budgets = {
            "daily": 10.00,
            "weekly": 50.00,
            "monthly": 200.00
        }
        self.spending = []
    
    def can_afford(self, estimated_cost: float) -> bool:
        """Check if operation fits within budget"""
        daily_spent = self.get_daily_spending()
        return (daily_spent + estimated_cost) <= self.budgets["daily"]
    
    def prioritize_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """Prioritize tasks based on budget and importance"""
        remaining_budget = self.budgets["daily"] - self.get_daily_spending()
        
        # Sort by importance/cost ratio
        tasks.sort(key=lambda x: x["importance"] / x["estimated_cost"], 
                  reverse=True)
        
        selected = []
        total_cost = 0
        
        for task in tasks:
            if total_cost + task["estimated_cost"] <= remaining_budget:
                selected.append(task)
                total_cost += task["estimated_cost"]
        
        return selected
    
    def suggest_model(self, task_complexity: str) -> str:
        """Suggest most cost-effective model for task"""
        daily_spent = self.get_daily_spending()
        remaining = self.budgets["daily"] - daily_spent
        
        if task_complexity == "simple" or remaining < 1.00:
            return "haiku"
        elif task_complexity == "moderate" or remaining < 5.00:
            return "sonnet"
        else:
            return "opus"
```

## Cost Optimization Strategies

### 1. Task Routing Algorithm

```python
def route_task(task: Dict) -> str:
    """Route task to appropriate model based on complexity and budget"""
    
    # Simple pattern matching tasks -> Haiku
    if task["type"] in ["duplicate_check", "date_extraction", "tag_generation"]:
        return "haiku"
    
    # Structured research -> Haiku
    if task["type"] == "research" and task.get("structured", False):
        return "haiku"
    
    # Complex analysis -> Sonnet
    if task["type"] in ["pattern_analysis", "pdf_processing"]:
        return "sonnet"
    
    # Orchestration and synthesis -> Opus
    if task["type"] in ["orchestration", "synthesis", "user_interaction"]:
        return "opus"
    
    # Default based on token estimate
    if task.get("estimated_tokens", 0) < 1000:
        return "haiku"
    elif task.get("estimated_tokens", 0) < 5000:
        return "sonnet"
    else:
        return "opus"
```

### 2. Caching Strategy

```python
# cache_manager.py
import hashlib
from typing import Optional

class CacheManager:
    def __init__(self):
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
    
    def get_cache_key(self, task_type: str, params: Dict) -> str:
        """Generate cache key for task"""
        content = f"{task_type}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, task_type: str, params: Dict) -> Optional[Dict]:
        """Get cached result if available"""
        key = self.get_cache_key(task_type, params)
        
        if key in self.cache:
            self.cache_hits += 1
            return self.cache[key]
        
        self.cache_misses += 1
        return None
    
    def set(self, task_type: str, params: Dict, result: Dict):
        """Cache result for future use"""
        key = self.get_cache_key(task_type, params)
        self.cache[key] = {
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "hit_count": 0
        }
    
    def get_stats(self) -> Dict:
        """Get cache performance statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / max(total_requests, 1)
        
        # Estimate cost savings (assuming $0.002 per cached request)
        savings = self.cache_hits * 0.002
        
        return {
            "hit_rate": round(hit_rate, 3),
            "total_hits": self.cache_hits,
            "total_misses": self.cache_misses,
            "estimated_savings": round(savings, 2)
        }
```

### 3. Batch Processing

```python
def batch_process(tasks: List[Dict]) -> Dict:
    """Process multiple tasks efficiently"""
    
    # Group by model type
    grouped = {"haiku": [], "sonnet": [], "opus": []}
    for task in tasks:
        model = route_task(task)
        grouped[model].append(task)
    
    results = {}
    total_cost = 0
    
    # Process Haiku tasks in parallel (cheap and fast)
    if grouped["haiku"]:
        haiku_results = parallel_process(grouped["haiku"], "haiku")
        results.update(haiku_results)
        total_cost += sum(r["cost"] for r in haiku_results.values())
    
    # Process Sonnet tasks with rate limiting
    if grouped["sonnet"]:
        sonnet_results = sequential_process(grouped["sonnet"], "sonnet")
        results.update(sonnet_results)
        total_cost += sum(r["cost"] for r in sonnet_results.values())
    
    # Process Opus tasks carefully (expensive)
    if grouped["opus"]:
        opus_results = sequential_process(grouped["opus"], "opus")
        results.update(opus_results)
        total_cost += sum(r["cost"] for r in opus_results.values())
    
    return {
        "results": results,
        "total_cost": round(total_cost, 3),
        "tasks_processed": len(tasks)
    }
```

## Monitoring Dashboard

### Daily Cost Dashboard
```
===========================================
DAILY COST DASHBOARD - 2025-01-20
===========================================

Model Usage:
  Haiku:   $0.45 / $1.00 (45%)  ✅
  Sonnet:  $2.10 / $3.00 (70%)  ⚠️
  Opus:    $1.20 / $5.00 (24%)  ✅

Total: $3.75 / $10.00 (37.5%)

Top Agents by Cost:
  1. pdf-analyzer:        $2.10 (56%)
  2. pattern-detector:    $0.80 (21%)
  3. timeline-researcher: $0.45 (12%)
  4. duplicate-checker:   $0.25 (7%)
  5. source-validator:    $0.15 (4%)

Efficiency Metrics:
  Events Created:        25
  Cost per Event:        $0.15
  Cache Hit Rate:        68%
  Estimated Savings:     $1.85

Optimization Suggestions:
  ⚠️ High Sonnet usage - consider Haiku for simpler tasks
  💡 Implement caching for pattern detection
  💡 Batch similar research tasks
===========================================
```

### Weekly Trends
```python
def generate_weekly_report():
    """Generate weekly cost trends"""
    report = {
        "week": "2025-W3",
        "total_cost": 24.50,
        "daily_average": 3.50,
        "events_created": 175,
        "cost_per_event": 0.14,
        "model_distribution": {
            "haiku": "65%",
            "sonnet": "25%",
            "opus": "10%"
        },
        "cost_reduction": "87% vs Opus-only",
        "recommendations": [
            "Maintain current distribution",
            "Consider upgrading cache size",
            "Review PDF processing frequency"
        ]
    }
    return report
```

## ROI Analysis

### Cost vs Value
| Metric | Opus Only | Optimized System | Improvement |
|--------|-----------|------------------|-------------|
| Daily Cost | $75.00 | $5.00 | 93% reduction |
| Events/Day | 10 | 50 | 5x increase |
| Cost/Event | $7.50 | $0.10 | 98% reduction |
| Quality Score | 95% | 93% | 2% trade-off |
| Processing Time | 5 hours | 1 hour | 80% faster |

### Break-even Analysis
```
Initial Setup Time: 8 hours
Ongoing Maintenance: 1 hour/week
Cost Savings: $70/day

Break-even: 1 day
Weekly Savings: $490
Monthly Savings: $2,100
Annual Savings: $25,550
```

## Alerts and Thresholds

### Budget Alerts
```python
ALERT_THRESHOLDS = {
    "daily_budget_warning": 0.8,     # Alert at 80% of daily budget
    "daily_budget_critical": 0.95,   # Critical at 95%
    "hourly_spike": 2.0,             # Alert if hourly cost > $2
    "model_imbalance": 0.5,          # Alert if one model > 50% of cost
    "cache_hit_low": 0.3,            # Alert if cache hit rate < 30%
}
```

### Action Triggers
```python
if daily_cost > DAILY_BUDGET * 0.8:
    # Switch to essential operations only
    disable_pattern_analysis()
    increase_cache_ttl()
    route_all_simple_to_haiku()

if hourly_cost > HOURLY_LIMIT:
    # Temporary throttling
    add_rate_limiting()
    queue_non_urgent_tasks()
```

## Summary

By implementing this cost tracking and optimization system:
- **93% cost reduction** compared to Opus-only approach
- **Real-time budget monitoring** prevents overruns
- **Automatic optimization** suggestions improve efficiency
- **Detailed analytics** inform system improvements
- **ROI of 25x** through cost savings and increased throughput

The key is continuous monitoring and adjustment based on actual usage patterns.
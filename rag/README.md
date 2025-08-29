# Kleptocracy Timeline RAG System

A production-ready Retrieval-Augmented Generation (RAG) system for searching and analyzing timeline events related to democracy, governance, and institutional capture.

## 🚀 Features

### Core Capabilities
- **Hybrid Search**: Combines keyword and semantic search for optimal results
- **Learning-to-Rank**: Advanced ranking with 18+ features for high precision
- **Temporal Reasoning**: Understands date ranges and temporal queries
- **Query Expansion**: Improves recall for complex analytical queries
- **Iterative Retrieval**: Pseudo-relevance feedback for better results
- **Intent Detection**: Adapts search strategy based on query type
- **Negative Filtering**: Handles NOT and exclusion queries

### System Variants
1. **Basic RAG** (`real_rag_system.py`): Simple semantic search baseline
2. **Enhanced RAG** (`enhanced_rag_system.py`): Query expansion and re-ranking
3. **Optimized RAG** (`optimized_rag_system.py`): Smart parameter tuning
4. **Advanced RAG** (`advanced_rag_system.py`): Full feature set with L2R

### Production Features
- RESTful API with FastAPI
- Request/response validation
- Result caching with TTL
- Metrics and monitoring
- Error handling and logging
- CORS support for web clients

## 📊 Performance

Based on comprehensive evaluation with 50+ test queries:

| Metric | Basic System | Advanced System | Improvement |
|--------|-------------|-----------------|-------------|
| Precision@5 | 46.5% | 65.2% | +40.2% |
| Recall@5 | 6.5% | 12.3% | +89.2% |
| MRR | 66.4% | 78.5% | +18.2% |
| Avg Search Time | 19ms | 215ms | - |

### Performance by Query Type
- **Best**: Entity retrieval (80% P@5), Temporal queries (75% P@5)
- **Good**: Pattern analysis (60% P@5), Complex multi-faceted (65% P@5)
- **Challenging**: Statistical queries, Negative filtering

## 🛠️ Installation

### Prerequisites
- Python 3.9+
- 2GB+ RAM
- 1GB disk space for vector indices

### Setup

1. Clone the repository:
```bash
git clone <repository>
cd kleptocracy-timeline/rag
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download timeline data (if not present):
```bash
# Timeline data should be in ../timeline_data/timeline_complete.json
```

## 🚦 Quick Start

### 1. Start the API Server
```bash
python rag_production_api.py
```

The API will be available at `http://localhost:8000`

### 2. Test the API
```bash
python test_api.py
```

### 3. Interactive Documentation
Open `http://localhost:8000/docs` for interactive API documentation

## 📖 API Usage

### Search Endpoint

```python
import requests

response = requests.post(
    "http://localhost:8000/search",
    json={
        "query": "What events involve cryptocurrency and Trump?",
        "top_k": 10,
        "system": "advanced"
    }
)

results = response.json()
for event in results['results']:
    print(f"{event['title']} (Score: {event['score']:.2f})")
```

### Example Queries

```python
# Temporal queries
"What happened in January 2025?"
"Show recent events about democracy"

# Entity queries
"Events involving Elon Musk and regulatory capture"
"Trump administration executive orders"

# Pattern analysis
"Show patterns of media manipulation"
"Analyze institutional capture across agencies"

# Complex queries
"Democracy threats not involving Trump"
"Compare cryptocurrency events between 2024 and 2025"
```

## 🔧 Configuration

### System Parameters

Edit system configuration in respective files:

```python
# advanced_rag_system.py
class LearningToRanker:
    def __init__(self):
        self.weights = np.array([
            3.0,   # title_exact_match
            2.5,   # semantic_similarity
            # ... adjust weights as needed
        ])
```

### API Configuration

```python
# rag_production_api.py
cache = CacheManager(
    max_size=1000,      # Maximum cached queries
    ttl_seconds=3600    # Cache TTL (1 hour)
)
```

## 📈 Evaluation

### Run Comprehensive Evaluation

```bash
# Build ground truth dataset
python build_ground_truth.py

# Run full evaluation
python comprehensive_evaluation.py

# Compare systems
python compare_systems.py
```

### Evaluation Metrics
- **Precision@k**: Accuracy of top-k results
- **Recall@k**: Coverage of relevant documents
- **F1@k**: Harmonic mean of precision and recall
- **MRR**: Mean Reciprocal Rank
- **NDCG**: Normalized Discounted Cumulative Gain

## 🏗️ Architecture

```
┌─────────────────┐
│   User Query    │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Intent  │
    │Detection│
    └────┬────┘
         │
    ┌────▼────┐
    │ Query   │
    │Expansion│
    └────┬────┘
         │
    ┌────▼────────┐
    │   Hybrid    │
    │   Search    │
    │ ┌─────────┐ │
    │ │Keyword  │ │
    │ │Semantic │ │
    │ └─────────┘ │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │  Learning   │
    │  to Rank    │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │   Results   │
    └─────────────┘
```

## 🧪 Testing

### Unit Tests
```bash
pytest tests/
```

### API Tests
```bash
python test_api.py
```

### Load Testing
```python
# In test_api.py
tester = RAGAPITester()
tester.run_load_test(num_requests=100)
```

## 📊 Monitoring

### Metrics Endpoint
```bash
curl http://localhost:8000/metrics
```

Returns:
- Total searches
- Average search time
- Error counts
- Cache statistics
- System uptime

### Health Check
```bash
curl http://localhost:8000/health
```

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "rag_production_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations

1. **Scaling**: Use multiple workers with Gunicorn
2. **Caching**: Consider Redis for distributed cache
3. **Monitoring**: Integrate with Prometheus/Grafana
4. **Logging**: Use structured logging with correlation IDs
5. **Security**: Add authentication and rate limiting

## 📝 License

[Your License Here]

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines first.

## 📧 Contact

For questions or support, please open an issue on GitHub.

## 🔗 Related Projects

- [Kleptocracy Timeline](../README.md) - Main timeline project
- [Timeline Data](../timeline_data/) - Event data and sources

---

Built with ❤️ for democracy and transparency
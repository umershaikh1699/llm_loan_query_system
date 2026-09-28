# Loan Portfolio Natural Language Query System

A backend system that allows credit and portfolio teams to interact with loan data using natural language instead of SQL or spreadsheets.

## System Overview

This system provides:
- Natural language interface to loan data via API
- Multi-turn conversation support with memory
- Structured JSON responses to queries
- MongoDB-style querying capabilities

## Directory Structure

```
/loan_query_system
├── api/
│   ├── __init__.py
│   └── endpoints.py
├── agent/
│   ├── __init__.py
│   └── query_agent.py
├── db/
│   ├── __init__.py
│   └── mock_db.py
├── app.py
└── requirements.txt
```

## Setup Instructions on Mac/Ubuntu

1. Clone the repository:
```bash
cd loan-query-system
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set your OpenAI API key if using OpenAI key Or Use Ollama Models:
```bash
export OPENAI_API_KEY=your_api_key_here
```
If Using ollama models:
```
Ollama(model="llama3:8b-instruct-q4_0", temperature=0)
```

5. Start the server:
```bash
python app.py
```

The API will be available at `http://localhost:8000`.

## API Endpoints

- `POST /query` - Submit a natural language query
- `GET /memory` - Retrieve conversation history
- `DELETE /memory` - Reset conversation history

## Sample Queries and Outputs

### Basic Query

**Request:**
```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"text": "What is the loan amount for Juan Perez?"}'
```

**Response:**
```json
{
  "result": 15000,
  "explanation": "I found Juan Perez in the database. His loan amount is 15000 COP."
}
```

### Intermediate Query

**Request:**
```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"text": "Total pending loan amount in COP?"}'
```

**Response:**
```json
{
  "result": 123456.78,
  "explanation": "I calculated the sum of all pending amounts for loans in COP currency."
}
```

### Advanced Query

**Request:**
```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"text": "Average loan for women in Central region"}'
```

**Response:**
```json
{
  "result": 20250.0,
  "explanation": "I calculated the average loan amount for female borrowers in the Central region. There are 2 such borrowers with an average loan amount of 20250.0."
}
```

### Multistep Query With Memory

**First Query:**
```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"text": "Group total loans by region and gender"}'
```

**Response:**
```json
{
  "result": [
    {"_id": {"region": "Central", "sex": "Female"}, "total_amount": 40500.0, "count": 2},
    {"_id": {"region": "Central", "sex": "Male"}, "total_amount": 15000.0, "count": 1},
    {"_id": {"region": "North", "sex": "Female"}, "total_amount": 92345.67, "count": 5},
    {"_id": {"region": "North", "sex": "Male"}, "total_amount": 84567.89, "count": 4},
    {"_id": {"region": "South", "sex": "Female"}, "total_amount": 76543.21, "count": 4},
    {"_id": {"region": "South", "sex": "Male"}, "total_amount": 95432.10, "count": 5},
    {"_id": {"region": "East", "sex": "Female"}, "total_amount": 123456.78, "count": 7},
    {"_id": {"region": "East", "sex": "Male"}, "total_amount": 112345.67, "count": 6},
    {"_id": {"region": "West", "sex": "Female"}, "total_amount": 89012.34, "count": 5},
    {"_id": {"region": "West", "sex": "Male"}, "total_amount": 97654.32, "count": 5}
  ],
  "explanation": "I grouped all loans by region and gender, then calculated the total loan amount and count for each group."
}
```

**Follow-up Query:**
```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"text": "Which region has the highest average loan amount?"}'
```

**Response:**
```json
{
  "result": "East",
  "explanation": "Based on the previous grouping, I calculated that the East region has the highest average loan amount of 17636.68 per loan."
}
```

### Retrieving Memory

**Request:**
```bash
curl -X GET "http://localhost:8000/memory"
```

**Response:**
```json
{
  "messages": [
    {"role": "human", "content": "Group total loans by region and gender"},
    {"role": "ai", "content": "..."},
    {"role": "human", "content": "Which region has the highest average loan amount?"},
    {"role": "ai", "content": "..."}
  ]
}
```

### Resetting Memory

**Request:**
```bash
curl -X DELETE "http://localhost:8000/memory"
```

**Response:**
```json
{
  "status": "Memory reset successfully"
}
```

## Testing with Python

You can also test the API using this Python script:

```python
import requests
import json

BASE_URL = "http://localhost:8000"

def query(text):
    response = requests.post(
        f"{BASE_URL}/query",
        json={"text": text}
    )
    return response.json()

def get_memory():
    response = requests.get(f"{BASE_URL}/memory")
    return response.json()

def reset_memory():
    response = requests.delete(f"{BASE_URL}/memory")
    return response.json()

# Example usage
print(json.dumps(query("What is the loan amount for Juan Perez?"), indent=2))
print(json.dumps(query("Average loan for women in Central region"), indent=2))
print(json.dumps(get_memory(), indent=2))
reset_memory()
```

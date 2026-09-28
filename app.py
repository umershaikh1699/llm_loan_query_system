from fastapi import FastAPI
from api.endpoints import setup_routes
from agents.query_agent import QueryAgent
from db.mock_db import LoanDatabase

app = FastAPI(
    title="Loan Query System",
    description="API for querying loan data using natural language",
    version="1.0.0",
)

# Initialize components
database = LoanDatabase()
query_agent = QueryAgent(database)

# Set up API routes
setup_routes(app, query_agent)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

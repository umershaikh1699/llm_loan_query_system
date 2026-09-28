from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.agents import Tool, ZeroShotAgent, AgentExecutor
from langchain_community.chat_models import ChatOllama
from typing import Dict, List, Any
import json
import re

class QueryAgent:
    def __init__(self, database):
        self.database = database
        self.memory = ConversationBufferMemory(return_messages=True)
        self.agent = self._create_agent()
    
    def _create_agent(self):
        tools = [
            Tool(
                name="find_loans",
                func=self._find_loans,
                description="Useful when you need to find specific loans or filter loans based on criteria."
            ),
            Tool(
                name="aggregate_loans",
                func=self._aggregate_loans,
                description="Useful when you need to group, sum, average or otherwise aggregate loan data."
            ),
            Tool(
                name="get_raw_data",
                func=self._get_raw_data,
                description="Useful when you need to see all loan data to analyze it yourself."
            ),
           Tool(
                name="greeting",
                func=self._handle_greeting,
                description="Use this to respond to greetings like hello/hi. Stops further processing.",
            )
        ]
        
        prefix = """You are an assistant for a loan portfolio manager.  
        The database fields are: user_name, region, sex, loan_amount.

        Follow these rules:  
        1. If the user greets (hi, hello, etc.), use the greeting tool ONCE and STOP.  
        2. For loan questions, pick the correct tool to query the database.  
        3. Return the answer as JSON with two fields: 'result' and 'explanation'.  

        Important:  
        - Output must start with 'Final Answer:'.  
        - Do NOT use any special formatting like code blocks or boxes."""
        
        suffix = """Begin!

        Question: {input}
        {agent_scratchpad}"""
        
        prompt = ZeroShotAgent.create_prompt(
            tools,
            prefix=prefix,
            suffix=suffix,
            input_variables=["input", "agent_scratchpad"]
        )
        
        llm = ChatOllama(model="granite3.3", temperature=0.1)
        llm_chain = LLMChain(llm=llm, prompt=prompt)
    
        agent = ZeroShotAgent(
            llm_chain=llm_chain,
            tools=tools,
            stop=["Final Answer:"],
            handle_parsing_errors=True,
        )
        
        return AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=tools,
            verbose=True,
            memory=self.memory,
            handle_parsing_errors=True,
            max_iterations=3,
            early_stopping_method="generate",
            return_intermediate_steps=False
        )
    
    def _handle_greeting(self, query_string: str = "") -> str:
        """Respond to greeting messages with properly formatted JSON"""
        greetings = ["hi", "hello", "hey", "greetings", "howdy"]
        query_string = str(query_string).lower().strip()
        
        response = {
            "result": "Hello! How can I help you with loan data today?" if query_string in greetings 
                    else f"I didn't recognize '{query_string}' as a greeting.",
            "explanation": "This is a friendly greeting response." if query_string in greetings
                        else "The input didn't match known greeting patterns."
        }
        # Return as string that will be parsed as final answer
        return f"Final Answer: {json.dumps(response)}"
    
    def _find_loans(self, query_string: str) -> str:
        """Execute a find operation based on natural language query"""
        try:
            # Parse the query to extract filters
            filter_dict = self._parse_filters(query_string)
            results = self.database.find(filter_dict)
            return json.dumps(results, indent=2)
        except Exception as e:
            return f"Error executing find: {str(e)}"
    
    def _aggregate_loans(self, query_string: str) -> str:
        """Execute an aggregation based on natural language query"""
        try:
            # Parse the query to build an aggregation pipeline
            
            pipeline = self._build_pipeline(query_string)
            results = self.database.aggregate(pipeline)
            return json.dumps(results, indent=2)
        except Exception as e:
            return f"Error executing aggregation: {str(e)}"
    
    def _get_raw_data(self, _: str) -> str:
        """Return all loan data"""
        try:
            results = self.database.raw_data()
            return json.dumps(results, indent=2)
        except Exception as e:
            return f"Error getting raw data: {str(e)}"
    
    def _parse_filters(self, query_string: str) -> Dict[str, Any]:
        """Parse a natural language query into a filter dictionary"""
        filters = {}
        
        # Extract user name if mentioned
        user_name_match = re.search(r"for\s+([A-Za-z\s]+)(?:\?|$|\s)", query_string)
        if user_name_match:
            filters["user_name"] = user_name_match.group(1).strip()
        
        # Extract region if mentioned
        region_match = re.search(r"in\s+(\w+)\s+region", query_string, re.IGNORECASE)
        if region_match:
            filters["region"] = region_match.group(1).capitalize()
        
        # Extract currency if mentioned
        currency_match = re.search(r"in\s+([A-Z]{3})", query_string)
        if currency_match:
            filters["currency"] = currency_match.group(1).upper()
        
        # Extract gender/sex if mentioned
        if "women" in query_string.lower() or "female" in query_string.lower():
            filters["sex"] = "Female"
        elif "men" in query_string.lower() or "male" in query_string.lower():
            filters["sex"] = "Male"
        
        return filters
    
    def _build_pipeline(self, query_string: str) -> List[Dict[str, Any]]:
        """Build an aggregation pipeline based on the query"""
        pipeline = []
        
        # Simple match stage
        match_stage = {"$match": {}}
        
        # Extract region if mentioned
        region_match = re.search(r"in\s+(\w+)\s+region", query_string, re.IGNORECASE)
        if region_match:
            match_stage["$match"]["region"] = region_match.group(1).capitalize()
        
        # Extract currency if mentioned
        currency_match = re.search(r"in\s+([A-Z]{3})", query_string)
        if currency_match:
            match_stage["$match"]["currency"] = currency_match.group(1).upper()
        
        # Extract gender/sex if mentioned
        if "women" in query_string.lower() or "female" in query_string.lower():
            match_stage["$match"]["sex"] = "Female"
        elif "men" in query_string.lower() or "male" in query_string.lower():
            match_stage["$match"]["sex"] = "Male"
        
        # Extract date comparison
        date_match = re.search(r"(before|after)\s+(\d{4})", query_string, re.IGNORECASE)
        if date_match:
            comparison, year = date_match.groups()
            year = int(year)
            if comparison.lower() == "before":
                match_stage["$match"]["disbursed_date"] = {"$lt": f"{year}-01-01"}
            else:
                match_stage["$match"]["disbursed_date"] = {"$gte": f"{year}-01-01"}
        
        if match_stage["$match"]:
            pipeline.append(match_stage)
        
        # Group stage for aggregations
        if "average" in query_string.lower() or "avg" in query_string.lower():
            group_stage = {
                "$group": {
                    "_id": None,
                    "average_loan": {"$avg": "$loan_amount"}
                }
            }
            pipeline.append(group_stage)
        
        elif "total" in query_string.lower() or "sum" in query_string.lower():
            field = "loan_amount"
            if "pending" in query_string.lower():
                field = "pending"
                
            group_stage = {
                "$group": {
                    "_id": None,
                    "total_amount": {"$sum": f"${field}"}
                }
            }
            pipeline.append(group_stage)
        
        elif "group" in query_string.lower():
            group_fields = {}
            
            if "region" in query_string.lower():
                group_fields["region"] = "$region"
            
            if "gender" in query_string.lower() or "sex" in query_string.lower():
                group_fields["sex"] = "$sex"
            
            if group_fields:
                group_stage = {
                    "$group": {
                        "_id": group_fields,
                        "total_amount": {"$sum": "$loan_amount"},
                        "count": {"$sum": 1}
                    }
                }
                pipeline.append(group_stage)
        
        # If no specific aggregation was identified, default to counting
        if len(pipeline) == 0 or (len(pipeline) == 1 and "$match" in pipeline[0]):
            group_stage = {
                "$group": {
                    "_id": None,
                    "count": {"$sum": 1}
                }
            }
            pipeline.append(group_stage)
        
        return pipeline
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process queries with proper greeting handling and clean JSON parsing."""
        try:
            response = self.agent.invoke({"input": query})
            
            # Handle direct tool responses (from return_direct=True)
            if isinstance(response, dict) and "output" in response:
                output = response["output"].strip()

                # Clean up "Thought:" or any text before 'Final Answer:'
                if 'Final Answer:' in output:
                    output = output.split('Final Answer:', 1)[1].strip()
                
                # Remove markdown code blocks if present
                if output.startswith('```json') or output.startswith('```'):
                    output = output.strip('`')  # remove backticks
                    output = output.replace('json', '', 1).strip()  # remove 'json' if present

                try:
                    return json.loads(output)
                except (json.JSONDecodeError, AttributeError) as e:
                    return {
                        "result": output,
                        "explanation": f"Parsing issue: {str(e)}"
                    }
            
            # Handle other response formats
            return {
                "result": str(response),
                "explanation": "System response"
            }
        
        except Exception as e:
            return {
                "error": str(e),
                "explanation": "Processing error occurred"
            }
    
    def get_memory(self) -> List[Dict[str, Any]]:
        """Return the current memory (conversation history)"""
        return self.memory.chat_memory.messages
    
    def reset_memory(self) -> Dict[str, str]:
        """Reset the conversation memory"""
        self.memory.clear()
        return {"status": "Memory reset successfully"}

import datetime
import random
import pandas as pd
from typing import Dict, List, Any


class LoanDatabase:
    def __init__(self):
        self.data = self._generate_mock_data()

    def _generate_mock_data(self) -> List[Dict[str, Any]]:
        """Generate a mock dataset with 50 loan records"""
        regions = ["North", "Central"]
        currencies = ["USD", "EUR", "COP"]

        data = []
        for i in range(1, 25):
            sex = random.choice(["Male", "Female"])
            disbursed_year = random.randint(2022, 2024)
            disbursed_month = random.randint(1, 12)
            disbursed_day = random.randint(1, 28)
            disbursed_date = datetime.date(
                disbursed_year, disbursed_month, disbursed_day
            )
            loan_term_years = random.randint(1, 3)
            due_date = datetime.date(
                disbursed_year + loan_term_years, disbursed_month, disbursed_day
            )
            loan_amount = round(random.uniform(1000, 50000), 2)
            pending_percentage = random.uniform(0, 1) if random.random() > 0.2 else 0
            pending = round(loan_amount * pending_percentage, 2)
            loan = {
                "id": i,
                "user_name": f"User {i}",
                "region": random.choice(regions),
                "sex": sex,
                "loan_amount": loan_amount,
                "currency": random.choice(currencies),
                "disbursed_date": disbursed_date.isoformat(),
                "due_date": due_date.isoformat(),
                "pending": pending,
            }
            data.append(loan)

        data[0]["user_name"] = "Juan Perez"
        data[0]["region"] = "Central"
        data[0]["sex"] = "Male"
        data[0]["loan_amount"] = 15000
        data[0]["currency"] = "EUR"

        data[1]["user_name"] = "Maria Rodriguez"
        data[1]["region"] = "Central"
        data[1]["sex"] = "Female"
        data[1]["loan_amount"] = 22000
        data[1]["currency"] = "USD"

        data[2]["user_name"] = "Ana Gomez"
        data[2]["region"] = "Central"
        data[2]["sex"] = "Female"
        data[2]["loan_amount"] = 18500
        data[2]["currency"] = "EUR"

        return data

    def query(self, query_func) -> List[Dict[str, Any]]:
        """Execute a query function against the database"""
        df = pd.DataFrame(self.data)
        result = query_func(df)

        if isinstance(result, pd.DataFrame):
            return result.to_dict("records")
        return result

    def find(self, filter_dict: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Find records matching the filter"""
        if filter_dict is None:
            return self.data

        results = []
        for record in self.data:
            match = True
            for key, value in filter_dict.items():
                if key not in record or record[key] != value:
                    match = False
                    break
            if match:
                results.append(record)

        return results

    def aggregate(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute MongoDB-style aggregation pipeline"""
        # Convert to pandas for easier manipulation
        df = pd.DataFrame(self.data)

        # For simplicity, we'll implement a subset of MongoDB aggregation
        result = df

        for stage in pipeline:
            # Match stage
            if "$match" in stage:
                for field, condition in stage["$match"].items():
                    if isinstance(condition, dict):
                        for op, value in condition.items():
                            if op == "$eq":
                                result = result[result[field] == value]
                            elif op == "$gt":
                                result = result[result[field] > value]
                            elif op == "$gte":
                                result = result[result[field] >= value]
                            elif op == "$lt":
                                result = result[result[field] < value]
                            elif op == "$lte":
                                result = result[result[field] <= value]
                    else:
                        result = result[result[field] == condition]

            # Group stage
            elif "$group" in stage:
                group_by = stage["$group"]["_id"]
                aggs = {k: v for k, v in stage["$group"].items() if k != "_id"}

                # Handle different _id formats
                if isinstance(group_by, dict):
                    # Composite key grouping
                    group_cols = list(group_by.values())
                else:
                    # Single field grouping
                    group_cols = [group_by]

                # Process aggregations
                agg_dict = {}
                for output_field, agg_expr in aggs.items():
                    for op, field_expr in agg_expr.items():
                        if op == "$sum":
                            if field_expr == 1:
                                agg_dict[output_field] = "count"
                            else:
                                agg_dict[output_field] = ("sum", field_expr)
                        elif op == "$avg":
                            agg_dict[output_field] = ("mean", field_expr)

                result = result.groupby(group_cols).agg(**agg_dict).reset_index()

            # Project stage
            elif "$project" in stage:
                fields = stage["$project"]
                include_fields = [k for k, v in fields.items() if v == 1]
                result = result[include_fields]

        return result.to_dict("records")

    def raw_data(self) -> List[Dict[str, Any]]:
        """Return the entire dataset"""
        return self.data

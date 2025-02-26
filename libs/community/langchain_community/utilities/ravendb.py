"""RavenDB wrapper around a database."""

from typing import Any, Dict, List, Optional, Union

from ravendb.documents.store.definition import DocumentStore
from ravendb.documents.session.document_session import DocumentSession
from ravendb.exceptions.raven_exceptions import RavenException
from ravendb.documents.operations.statistics import GetCollectionStatisticsOperation

class RavenDB:
    """RavenDB wrapper around a database."""

    def __init__(
        self,
        url: str,
        database_name: str,
        cert_path: Optional[str] = None
    ):
        """Initialize the RavenDBTool with connection details."""
        self.store = DocumentStore(urls=[url], database=database_name)
        self.store.initialize()
        self.schema = self.get_schema()

    def get_schema(self) -> Dict[str, Any]:
        """Retrieve the database schema."""
        schema = {}
        with self.store as store:
            collections = store.maintenance.send(GetCollectionStatisticsOperation())
            collections = [collection['Name'] for collection in collections]
            schema = collections
        return schema

    def execute_query(self, query_text: str) -> List[Dict[str, Any]]:
        """Execute a RavenDB query and return the results."""
        with self.store.open_session() as session:
            results = session.advanced.raw_query(query_text).to_list()
        return results

    def execute(
        self,
        query_text: str,
        fetch: str = "all",
        include_columns: bool = False,
    ) -> Union[str, List[Dict[str, Any]]]:
        """Execute a query and return the results."""
        try:
            results = self.execute_query(query_text)
            if not include_columns:
                results = [tuple(row.values()) for row in results]
            return results
        except RavenException as e:
            return f"Error: {e}"

    def get_context(self) -> Dict[str, Any]:
        """Return db context that you may want in agent prompt."""
        return {"schema": self.schema}

# Example usage
# ravendb = RavenDB(
#     url="https://your-ravendb-url",
#     database_name="your-database-name",
#     cert_path="/path/to/your/certificate"
# )
# results = ravendb.execute("from Orders where Amount > 100")
# print(results)

# # Using LangGraph
# def execute_ravendb_query(agent, query_text):
#     results = agent.execute(query_text)
#     return results

# # Example usage with LangGraph
# # Assuming you have a LangGraph instance
# query_text = "from Orders where Amount > 100"
# results = execute_ravendb_query(raven_tool, query_text)
# print(results)

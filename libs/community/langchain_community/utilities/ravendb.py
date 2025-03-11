"""RavenDB wrapper around a database."""

from typing import Any, Dict, List, Optional, Union

from ravendb.documents.store.definition import DocumentStore
from ravendb.documents.session.document_session import DocumentSession
from ravendb.exceptions.raven_exceptions import RavenException
from ravendb.documents.operations.statistics import GetCollectionStatisticsOperation

class DocumentStoreHolder:
    """Singleton holder for the DocumentStore instance."""
    _instance: Optional[DocumentStore] = None
    _url: Optional[str] = None
    _database_name: Optional[str] = None
    _cert_path: Optional[str] = None

    @classmethod
    def configure(cls, url: str, database_name: str, cert_path: Optional[str] = None):
        cls._url = url
        cls._database_name = database_name
        cls._cert_path = cert_path

    @classmethod
    def get_store(cls) -> DocumentStore:
        if cls._instance is None:
            if cls._url is None or cls._database_name is None:
                raise ValueError("DocumentStoreHolder is not configured with URL and database name.")
            cls._instance = DocumentStore(urls=[cls._url], database=cls._database_name)
            cls._instance.certificate_pem_path = cls._cert_path
            cls._instance.initialize()
        return cls._instance

class RavenDB:
    """RavenDB wrapper around a database."""

    def __init__(self):
        """Initialize the RavenDBTool with connection details."""
        self.store = DocumentStoreHolder.get_store()
        # self.schema = self.get_collection_info([])  # Pass an empty list as the default value``

    def to_dict(self, obj):
        if isinstance(obj, dict):
            return {k: self.to_dict(v) for k, v in obj.items()}
        elif hasattr(obj, "__dict__"):
            return {k: self.to_dict(v) for k, v in obj.__dict__.items()}
        else:
            return obj

    def get_collection_info(self, collection_names: List[str]) -> Dict[str, Any]:
        """Retrieve collections and sample documents."""
        schema = {}
        with self.store as store:
            collection_stats = store.maintenance.send(GetCollectionStatisticsOperation()).collections
            with store.open_session() as session:
                for key in collection_stats.keys():
                    if not collection_names or key in collection_names:
                        # Query the first document in the collection
                        first_document = session.query_collection(key).first()
                        schema[key] = self.to_dict(first_document)
        print(schema)
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
# results = ravendb.execute("from @collection_names")
# print(results)

# Using LangGraph
# def execute_ravendb_query(agent, query_text):
#     results = agent.execute(query_text)
#     return results

# Example usage with LangGraph
# Assuming you have a LangGraph instance
# query_text = "from Orders where Amount > 100"
# results = ravendb.execute(query_text)
# print(results)

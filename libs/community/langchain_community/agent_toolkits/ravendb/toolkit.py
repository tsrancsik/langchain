"""Toolkit for interacting with a RavenDB database."""

from typing import List

from langchain_core.caches import BaseCache as BaseCache
from langchain_core.callbacks import Callbacks as Callbacks
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool
from langchain_core.tools.base import BaseToolkit
from pydantic import ConfigDict, Field

from langchain_community.tools.sql_database.tool import (
    InfoSQLDatabaseTool,
    ListSQLDatabaseTool,
    QuerySQLCheckerTool,
    QuerySQLDatabaseTool,
)
from langchain_community.tools.ravendb.tool import (
    QueryRavenDBTool as QueryRavenDBBaseTool,  # keep import for backwards compat.
)
from langchain_community.utilities.ravendb import RavenDB


class RavenDBToolkit(BaseToolkit):
    """SQLDatabaseToolkit for interacting with SQL databases.

    Setup:
        Install ``langchain-community``.

        .. code-block:: bash

            pip install -U langchain-community

    Key init args:
        db: SQLDatabase
            The SQL database.
        llm: BaseLanguageModel
            The language model (for use with QuerySQLCheckerTool)

    Instantiate:
        .. code-block:: python

            from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
            from langchain_community.utilities.sql_database import SQLDatabase
            from langchain_openai import ChatOpenAI

            db = RavenDB(
                url="https://your-ravendb-url",
                database_name="your-database-name",
                cert_path="/path/to/your/certificate",
                api_key="YOUR_API_KEY"
            )
            llm = ChatOpenAI(temperature=0)

            toolkit = RavenDBToolkit(db=db, llm=llm)

    Tools:
        .. code-block:: python

            toolkit.get_tools()

    Use within an agent:
        .. code-block:: python

            from langchain import hub
            from langgraph.prebuilt import create_react_agent

            # Pull prompt (or define your own)
            prompt_template = hub.pull("langchain-ai/sql-agent-system-prompt")
            system_message = prompt_template.format(dialect="SQLite", top_k=5)

            # Create agent
            agent_executor = create_react_agent(
                llm, toolkit.get_tools(), state_modifier=system_message
            )

            # Query agent
            example_query = "Which country's customers spent the most?"

            events = agent_executor.stream(
                {"messages": [("user", example_query)]},
                stream_mode="values",
            )
            for event in events:
                event["messages"][-1].pretty_print()
    """  # noqa: E501

    db: RavenDB = Field(exclude=True)
    llm: BaseLanguageModel = Field(exclude=True)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    def get_tools(self) -> List[BaseTool]:
        """Get the tools in the toolkit."""
        list_ravendb_tool = ListRavenDBTool(db=self.db)
        info_ravendb_tool_description = (
            "Input to this tool is a comma-separated list of collections, output is the "
            "schema and sample rows for those tables. "
            "Be sure that the collections actually exist by calling "
            f"{list_ravendb_tool.name} first! "
            "Example Input: collection1, collection2, collection3"
        )
        info_sql_database_tool = InfoSQLDatabaseTool(
            db=self.db, description=info_ravendb_tool_description
        )
        query_ravendb_tool_description = (
            "Input to this tool is a detailed and correct RQL query, output is a "
            "result from the database. If the query is not correct, an error message "
            "will be returned. If an error is returned, rewrite the query, check the "
            "query, and try again. If you encounter an issue with Unknown field "
            f"'xxxx' in 'field list', use {info_ravendb_tool.name} "
            "to query the correct table fields."
        )
        query_sql_database_tool = QuerySQLDatabaseTool(
            db=self.db, description=query_sql_database_tool_description
        )
        query_rql_checker_tool_description = (
            "Use this tool to double check if your query is correct before executing "
            "it. Always use this tool before executing a query with "
            f"{query_ravendb_tool.name}!"
        )
        query_rql_checker_tool = QueryRQLCheckerTool(
            db=self.db, llm=self.llm, description=query_rql_checker_tool_description
        )
        return [
            query_ravendb_tool,
            info_ravendb_tool,
            list_ravendb_tool,
            query_rql_checker_tool,
        ]

    def get_context(self) -> dict:
        """Return db context that you may want in agent prompt."""
        return self.db.get_context()


RavenDBToolkit.model_rebuild()

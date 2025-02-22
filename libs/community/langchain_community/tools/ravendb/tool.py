# flake8: noqa
"""Tools for interacting with a RavenDB database."""

from typing import Any, Dict, Optional, Sequence, Type, Union

from pydantic import BaseModel, Field, root_validator, model_validator, ConfigDict

from langchain_core._api.deprecation import deprecated
from langchain_core.language_models import BaseLanguageModel
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.prompts import PromptTemplate
from langchain_community.utilities.ravendb import RavenDB
from langchain_core.tools import BaseTool
from langchain_community.tools.ravendb.prompt import QUERY_CHECKER


class BaseRavenDBTool(BaseModel):
    """Base tool for interacting with a RavenDB database."""

    db: RavenDB = Field(exclude=True)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class _QueryRavenDBToolInput(BaseModel):
    query: str = Field(..., description="A detailed and correct RQL query.")


class QueryRavenDBTool(BaseRavenDBTool, BaseTool):  # type: ignore[override, override]
    name: str = "ravendb_query"
    description: str = """
    Execute an RQL query against the database and get back the result..
    If the query is not correct, an error message will be returned.
    If an error is returned, rewrite the query, check the query, and try again.
    """
    args_schema: Type[BaseModel] = _QueryRavenDBToolInput

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Union[str, Sequence[Dict[str, Any]], Result]:
        """Execute the query, return the results or an error message."""
        return self.db.run_no_throw(query)


class _InfoRavenDBToolInput(BaseModel):
    collection_names: str = Field(
        ...,
        description=(
            "A comma-separated list of the collections names for which to return the schema. "
            "Example input: 'collection1, collection2, collection3'"
        ),
    )


class InfoRavenDBTool(BaseRavenDBTool, BaseTool):  # type: ignore[override, override]
    """Tool for getting metadata about a RavenDB database."""

    name: str = "ravendb_schema"
    description: str = "Get the schema and sample documents for the specified Ravendb collections."
    args_schema: Type[BaseModel] = _InfoRavenDBToolInput

    def _run(
        self,
        collection_names: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Get the schema for colelctions in a comma-separated list."""
        return self.db.get_collection_info_no_throw(
            [t.strip() for t in collection_names.split(",")]
        )


class _ListRavenDBToolInput(BaseModel):
    tool_input: str = Field("", description="An empty string")


class ListRavenDBTool(BaseRavenDBTool, BaseTool):  # type: ignore[override, override]
    """Tool for getting collection names."""

    name: str = "ravendb_list_collections"
    description: str = "Input is an empty string, output is a comma-separated list of collections in the database."
    args_schema: Type[BaseModel] = _ListRavenDBToolInput

    def _run(
        self,
        tool_input: str = "",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Get a comma-separated list of collection names."""
        return ", ".join(self.db.get_usable_collection_names())


class _QueryRQLCheckerToolInput(BaseModel):
    query: str = Field(..., description="A detailed and RQL query to be checked.")


class QueryRQLCheckerTool(BaseRQLDatabaseTool, BaseTool):  # type: ignore[override, override]
    """Use an LLM to check if a query is correct.
    Adapted from https://www.patterns.app/blog/2023/01/18/crunchbot-sql-analyst-gpt/"""

    template: str = QUERY_CHECKER
    llm: BaseLanguageModel
    llm_chain: Any = Field(init=False)
    name: str = "ravendb_query_checker"
    description: str = """
    Use this tool to double check if your query is correct before executing it.
    Always use this tool before executing a query with ravendb_query!
    """
    args_schema: Type[BaseModel] = _QueryRQLCheckerToolInput

    @model_validator(mode="before")
    @classmethod
    def initialize_llm_chain(cls, values: Dict[str, Any]) -> Any:
        if "llm_chain" not in values:
            from langchain.chains.llm import LLMChain

            values["llm_chain"] = LLMChain(
                llm=values.get("llm"),  # type: ignore[arg-type]
                prompt=PromptTemplate(
                    template=QUERY_CHECKER, input_variables=["query"]
                ),
            )

        if values["llm_chain"].prompt.input_variables != ["query"]:
            raise ValueError(
                "LLM chain for QueryCheckerTool must have input variable 'query'"
            )

        return values

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the LLM to check the query."""
        return self.llm_chain.predict(
            query=query,
            callbacks=run_manager.get_child() if run_manager else None,
        )

    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        return await self.llm_chain.apredict(
            query=query,
            callbacks=run_manager.get_child() if run_manager else None,
        )

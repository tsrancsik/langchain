from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, TypedDict, Union

from langchain_core.language_models import BaseLanguageModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import BasePromptTemplate
from langchain_core.runnables import Runnable, RunnablePassthrough

from langchain.chains.ravendb.prompt import PROMPT

if TYPE_CHECKING:
    from langchain_community.utilities.ravendb import RavenDB


def _strip(text: str) -> str:
    return text.strip()


class RQLInput(TypedDict):
    """Input for a RavenDB Chain."""

    question: str


class RQLInputWithCollections(TypedDict):
    """Input for a RavenDB Chain."""

    question: str
    collection_names_to_use: List[str]


def create_rql_query_chain(
    llm: BaseLanguageModel,
    db: RavenDB,
    prompt: Optional[BasePromptTemplate] = None,
    k: int = 5,
) -> Runnable[Union[RQLInput, RQLInputWithCollections, Dict[str, Any]], str]:
    """Create a chain that generates RavenDB RQL queries.

    *Security Note*: This chain generates RavenDB RQL queries for the given database.

        The RavenDB class provides a get_collection_info method that can be used
        to get field information as well as sample data from the table.

        To mitigate risk of leaking sensitive data, limit permissions
        to read and scope to the tables that are needed.

        Optionally, use the RQLInputWithCollections input type to specify which tables
        are allowed to be accessed.

        Control access to who can submit requests to this chain.

        See https://python.langchain.com/docs/security for more information.

    Args:
        llm: The language model to use.
        db: The RavenDB to generate the query for.
        prompt: The prompt to use. If none is provided, will choose one.
            Defaults to None. See Prompt section below for more.
        k: The number of results per select statement to return. Defaults to 5.

    Returns:
        A chain that takes in a question and generates a RavenDB RQL query that answers
        that question.

    Example:

        .. code-block:: python

            # pip install -U langchain langchain-community langchain-openai
            from langchain_openai import ChatOpenAI
            from langchain.chains import create_rql_query_chain
            from langchain_community.utilities import RavenDB

            ravendb = RavenDB(
                urls=["https://your-ravendb-url"],
                database_name="your-database-name",
                cert_path="/path/to/your/certificate",
                api_key="YOUR_API_KEY"
            )
            llm = ChatOpenAI(model="gpt-4o", temperature=0)
            chain = create_rql_query_chain(llm, ravendb)
            response = chain.invoke({"question": "How many employees are there"})

    Prompt:
        If no prompt is provided, a default prompt is selected based. If one is provided, it must support input variables:
            * input: The user question plus suffix "\nRQLQuery: " is passed here.
            * top_k: The number of results per select statement (the `k` argument to
                this function) is passed in here.
            * collection_info: Collection definitions and sample rows are passed in here. If the
                user specifies "collection_names_to_use" when invoking chain, only those
                will be included. Otherwise, all collections are included.
        Here's an example prompt:

        .. code-block:: python

            from langchain_core.prompts import PromptTemplate

            template = '''Given an input question, first create a syntactically correct RavenDB RQL query to run, then look at the results of the query and return the answer.
            Use the following format:

            Question: "Question here"
            RQLQuery: "RQL Query to run"
            RQLResult: "Result of the RQLQuery"
            Answer: "Final answer here"

            Only use the following collections:

            {collection_info}.

            Question: {input}'''
            prompt = PromptTemplate.from_template(template)
    """

    if prompt is not None:
        prompt_to_use = prompt
    else:
        prompt_to_use = PROMPT
    if {"input", "top_k", "collection_info"}.difference(
        prompt_to_use.input_variables + list(prompt_to_use.partial_variables)
    ):
        raise ValueError(
            f"Prompt must have input variables: 'input', 'top_k', "
            f"'collection_info'. Received prompt with input variables: "
            f"{prompt_to_use.input_variables}. Full prompt:\n\n{prompt_to_use}"
        )

    inputs = {
        "input": lambda x: x["question"] + "\nRQLQuery: ",
        "collection_info": lambda x: db.get_collection_info(
            collection_names=x.get("collection_names_to_use")
        ),
    }
    return (
        RunnablePassthrough.assign(**inputs)  # type: ignore
        | (
            lambda x: {
                k: v
                for k, v in x.items()
                if k not in ("question", "collection_names_to_use")
            }
        )
        | prompt_to_use.partial(top_k=str(k))
        | llm.bind(stop=["\nRQLResult:"])
        | StrOutputParser()
        | _strip
    )

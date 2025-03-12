# flake8: noqa
from langchain_core.output_parsers.list import CommaSeparatedListOutputParser
from langchain_core.prompts.prompt import PromptTemplate


PROMPT_SUFFIX = """Only use the following tables:
{collection_info}

Question: {input}"""

_DEFAULT_TEMPLATE = """Given an input question, first create a syntactically correct RavenDB RQL query to run, then look at the results of the query and return the answer. Unless the user specifies in his question a specific number of examples he wishes to obtain, always limit your query to at most {top_k} results. You can order the results by a relevant column to return the most interesting examples in the database.

An example of the correct format is as follows:
from Orders
group by Employee
order by count() desc
select Employee, count() as OrderCount
limit 5

Never query for all the attributes of the documents from a specific collection, only ask for a the few relevant attributes given the question.

Pay attention to use only the attribute names that you can see in the schema description. Be careful to not query for attributes that do not exist. Also, pay attention to which column is in which table.

Use the following format:

Question: Question here
RQLQuery: RQL Query to run
RQLResult: Result of the RQLQuery
Answer: Final answer here

"""

PROMPT = PromptTemplate(
    input_variables=["input", "collection_info", "top_k"],
    template=_DEFAULT_TEMPLATE + PROMPT_SUFFIX,
)


_DECIDER_TEMPLATE = """Given the below input question and list of potential collections, output a comma separated list of the collection names that may be necessary to answer this question.

Question: {query}

Collection Names: {collection_names}

Relevant Table Names:"""
DECIDER_PROMPT = PromptTemplate(
    input_variables=["query", "collection_names"],
    template=_DECIDER_TEMPLATE,
    output_parser=CommaSeparatedListOutputParser(),
)

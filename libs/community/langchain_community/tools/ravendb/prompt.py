QUERY_CHECKER = """
{query}
Double check the RavenDB query above for common mistakes, including:
- Data type mismatch in predicates
- Properly quoting identifiers
- Using the correct number of arguments for functions
- Casting to the correct data type
- Using the proper columns for joins

If there are any of the above mistakes, rewrite the query. If there are no mistakes, just reproduce the original query.

Output the final RQL query only.

RQL Query: """

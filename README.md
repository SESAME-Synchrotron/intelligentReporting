#  Intelligent Reporting: RDF-based Modeling and LLM-Powered Report Generation from Relational Databases

This project aims to develop a solution based on MDE and LLMs for automatically generating reports from relational databases. The core idea is to allow users to provide high-level, human-readable descriptions to the MDE component, which will then automatically connect to the target database, generate appropriate SQL queries, and return the results.

For the LLM to generate accurate SQL queries, it must first understand the structure of the underlying database. To facilitate this, the relational database schema is represented as a Knowledge Graph (KG) constructed using the Resource Description Framework (RDF), based on mappings defined in the Relational to RDF Mapping Language (R2RML). 

R2RML is a W3C-recommended language for expressing customized mappings from relational databases to RDF datasets. R2RML enables the transformation of structured data—such as tables, rows, fron and primary keys and columns into RDF triples (see https://www.w3.org/TR/r2rml/).

Also XMLSchema is another W3C standard that is used to define the structure and constraints of XML documents. It supports specifying:
- The data types of elements and attributes (e.g., string, integer, date),
- The order and cardinality of elements,
- Rules for nesting elements and referencing other types.

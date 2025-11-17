from rdflib import Graph, RDFS, XSD, OWL

def ttlToRelationalSchema(ttlFile: str):
    g = Graph()
    g.parse(ttlFile, format='ttl')

    # 1) Discover classes → tables
    tables = {}
    for cls in g.subjects(RDF.type, RDFS.Class):
        name = cls.split('#')[-1]
        tables[name] = {"columns": {}, "pks": [], "fks": []}

    # 2) Discover datatype properties → columns
    for prop in g.subjects(RDF.type, OWL.DatatypeProperty):
        dom = g.value(prop, RDFS.domain)
        rng = g.value(prop, RDFS.range)
        tbl = dom.split('#')[-1]
        col = prop.split('#')[-1]
        typ = rng.split('#')[-1] if rng and rng==XSD.string else "TEXT"
        tables[tbl]["columns"][col] = typ

    # 3) Discover object properties → foreign keys
    for prop in g.subjects(RDF.type, OWL.ObjectProperty):
        dom = g.value(prop, RDFS.domain)
        rng = g.value(prop, RDFS.range)
        tbl = dom.split('#')[-1]
        ref = rng.split('#')[-1]
        col = prop.split('#')[-1] + "_id"
        tables[tbl]["columns"][col] = "INTEGER"
        tables[tbl]["fks"].append((col, ref + "(id)"))

    # 4) Mark “id” as primary key on every table
    for t in tables:
        tables[t]["columns"]["id"] = "INTEGER"
        tables[t]["pks"].append("id")

    return tables

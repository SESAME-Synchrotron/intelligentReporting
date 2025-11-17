import rdflib
from urllib.parse import urlparse
class structuredRDFKG: 
    def __init__(self, baseNameSpace):
        self.base = baseNameSpace
        # self.baseName = baseNameSpace.split('/')[-2] # to get last part of the namespace
        self.baseName = baseNameSpace
        self.baseNameSpace = rdflib.Namespace (baseNameSpace)
        self.graph = rdflib.Graph()
        self.addMainSchemas()
    
    def addMainSchemas(self):
        self.RR = rdflib.Namespace('http://www.w3.org/ns/r2rml#')
        self.XSD = rdflib.Namespace('http://www.w3.org/2001/XMLSchema#')
        self.graph.bind('ns', self.baseNameSpace) # main name space
        self.graph.bind('rr', self.RR) 
        self.graph.bind('xsd', self.XSD)
    
    def mapSQLType(self, sql_type):
        recType = sql_type.upper()
        if (recType.startswith('NVARCHAR') or recType.startswith('VARCHAR') or
            recType.startswith('CHAR') or recType.startswith('TEXT')):
            return 'string'
        elif (recType.startswith('INTEGER') or recType.startswith('INT') or 
            recType.startswith('BIGINT') or recType.startswith('SMALLINT') or 
            recType.startswith('TINYINT')):
            return 'integer'
        elif (recType.startswith('FLOAT') or recType.startswith('DOUBLE') or 
            recType.startswith('REAL')):
            return 'float'
        elif recType.startswith('DECIMAL') or recType.startswith('NUMERIC'):
            return 'decimal'
        elif recType.startswith('DATETIME'):
            return 'dateTime'
        elif recType.startswith('DATE'):
            return 'date'
        elif recType.startswith('TIME'):
            return 'time'
        elif recType.startswith('BOOLEAN') or recType.startswith('BIT'):
            return 'boolean'
        elif recType.startswith('BLOB') or recType.startswith('BINARY'):
            return 'binary'
        return sql_type


    def addTable (self, tableName):
        # tableMap = rdflib.URIRef('#'+tableName+'TriplesMap')
        tableMap = rdflib.URIRef('#'+tableName+'TriplesMap')
        logicalTable = rdflib.BNode()
        self.graph.add((tableMap, self.RR.logicalTable, logicalTable))
        self.graph.add((logicalTable, self.RR.tableName, rdflib.Literal(tableName)))
        
    def addColumn(self, tableName, columnName, columnType, pk):
        tableMap = rdflib.URIRef('#' + tableName + 'TriplesMap')
        if pk == 1:
            subjectMap = rdflib.BNode()
            self.graph.add((tableMap, self.RR.subjectMap, subjectMap))
            self.graph.add((
                subjectMap,
                self.RR.template,
                rdflib.Literal(self.baseName + tableName + '/{' + columnName + '}')
            ))
            self.graph.add((
                subjectMap,
                self.RR['class'],
                self.baseNameSpace[tableName]
            ))
            predObjMap = rdflib.BNode()
            self.graph.add((tableMap, self.RR.predicateObjectMap, predObjMap))
            self.graph.add((predObjMap, self.RR.predicate, self.baseNameSpace[columnName]))
            objMap = rdflib.BNode()
            self.graph.add((predObjMap, self.RR.objectMap, objMap))
            self.graph.add((objMap, self.RR.column, rdflib.Literal(columnName)))
            self.graph.add((objMap, self.RR.datatype, self.XSD[self.mapSQLType(columnType)]))
        elif pk == 0:
            predObjMap = rdflib.BNode()
            self.graph.add((tableMap, self.RR.predicateObjectMap, predObjMap))
            self.graph.add((predObjMap, self.RR.predicate, self.baseNameSpace[columnName]))
            objMap = rdflib.BNode()
            self.graph.add((predObjMap, self.RR.objectMap, objMap))
            self.graph.add((objMap, self.RR.column, rdflib.Literal(columnName)))
            self.graph.add((objMap, self.RR.datatype, self.XSD[self.mapSQLType(columnType)]))

    # def addForeignKey(self, sourceTable, sourceColumn, targetTable, targetColumn, predicateLocalName):
    #     pom = rdflib.BNode()  # predicateObjectMap
    #     objectMap = rdflib.BNode()
    #     joinCondition = rdflib.BNode()
    #     triplesMap = rdflib.URIRef(f"{self.baseNameSpace}{sourceTable}TriplesMap")
    #     self.graph.add((triplesMap, self.RR.predicateObjectMap, pom))
    #     self.graph.add((pom, self.RR.predicate, self.baseNameSpace[predicateLocalName]))
    #     self.graph.add((pom, self.RR.objectMap, objectMap))
    #     self.graph.add((objectMap, self.RR.parentTriplesMap, rdflib.URIRef(f"{self.baseNameSpace}{targetTable}TriplesMap")))
    #     self.graph.add((objectMap, self.RR.joinCondition, joinCondition))
    #     self.graph.add((joinCondition, self.RR.child, rdflib.Literal(sourceColumn)))
    #     self.graph.add((joinCondition, self.RR.parent, rdflib.Literal(targetColumn)))
    def addForeignKey(self, sourceTable, sourceColumn, targetTable, targetColumn, predicateLocalName=None):
        from rdflib import BNode, URIRef, Literal
        if predicateLocalName is None:
            predicateLocalName = f"{sourceColumn}_to_{targetTable}"

        pom = BNode()
        objectMap = BNode()
        joinCondition = BNode()

        triplesMap = URIRef(f"{self.baseNameSpace}{sourceTable}TriplesMap")

        self.graph.add((triplesMap, self.RR.predicateObjectMap, pom))
        self.graph.add((pom, self.RR.predicate, self.baseNameSpace[predicateLocalName]))
        self.graph.add((pom, self.RR.objectMap, objectMap))
        self.graph.add((objectMap, self.RR.parentTriplesMap, URIRef(f"{self.baseNameSpace}{targetTable}TriplesMap")))
        self.graph.add((objectMap, self.RR.joinCondition, joinCondition))
        self.graph.add((joinCondition, self.RR.child, Literal(sourceColumn)))
        self.graph.add((joinCondition, self.RR.parent, Literal(targetColumn)))
        
    def saveRDF(self, filename):
        self.graph.serialize(destination=filename, format='turtle')
        
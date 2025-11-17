# Notes: 
# ----------------------------------------------------------------------
# shortcuts and tags:
#   _AN: Action needed -> means that to do later
#   _IMPORTANT: means inportant instructions you have to follow (explcitly)


from db_sqllite import DBSQLITE
from db_postgres import DBPostgres
from support import findDB
from kg import structuredRDFKG
import os


databasesConfig = findDB('DBConfig.yml')
DBParameters = databasesConfig.loadConfig()
databasesConfig.pringParams()
kGraph = structuredRDFKG(DBParameters['databases'][0]['KGNameSpace'])
    
for db in DBParameters['databases']:
    DBServer = db['name']
    DBEngine = db['engine']
    connectionDetails = db['connection_details']
    if DBEngine == 'sqlite3':
        for db_file in connectionDetails['database_files']:
            DBName = os.path.splitext(os.path.basename(db_file))[0]
            db_instance = DBSQLITE(db_file)
            tables = db_instance.getTableNames() # returns a list of tuples        
        
            # get more structural info about the tables
            # _IMPORTANT: logic of adding to graph is add (first)table, (second) columns, (third) foreign keys
            for table in tables:
                # kGraph.addEntity(table[0], 'Table', {})
                kGraph.addTable(table[0])
                tableColumns = db_instance.getTableColumns(table[0])
                print ('--------------------')
                print('tableColumns: ',tableColumns)
                print ('--------------------')
                for xx in tableColumns:
                    # column format is (cid, name, type, notnull, default_value, primary_key)
                    kGraph.addColumn(table[0], xx[1], xx[2],xx[5])
                    
                    pass 
                foreign_keys = db_instance.getForeignKeys(table[0])
                print('foreign_keys:', foreign_keys)
                if foreign_keys:
                    print(f"Foreign keys for table '{table[0]}':")
                    for fk in foreign_keys:
                        # fk format is (0id, 1seq, 2fk_table, 3fk_column, 4pk_table, 5pk_column)
                        kGraph.addForeignKey( table[0],fk[3], fk[2],fk[4])
                        print(f"  Column {fk[3]} references {fk[2]}.{fk[4]}")
                else:
                    print(f"No foreign keys for table '{table[0]}'")
                print ('table[0]', table[0])

    elif DBEngine == 'postgres':
        DBName = connectionDetails['database']
        db_instance = DBPostgres(connectionDetails['database'], connectionDetails['username'], 
                                 connectionDetails['password'], connectionDetails['host'], 
                                 connectionDetails['port'])
        tables = db_instance.getTableNames()
        print ('###################')
        print (tables)
        print ('###################')
        for table in tables:
            print ('###################')
            kGraph.addTable(table[0])
            tableColumns = db_instance.getTableColumns(table[0])
            print('tableColumns: ',tableColumns)
            for column in tableColumns:
                # column format is (cid, name, type, notnull, default_value, primary_key)
                kGraph.addColumn(table[0], column[0], column[1])
                pass
            foreign_keys = db_instance.getForeignKeys(table[0])
            # foreign_keys: [('playlist_track_playlist_id_fkey', 'playlist_id', 'playlist', 'playlist_id')]
            if foreign_keys:
                print(f"Foreign keys for table '{table[0]}':")
                for fk in foreign_keys:
                    # [('playlist_track_playlist_id_fkey', 'playlist_id', 'playlist', 'playlist_id')]              
                    kGraph.addForeignKey( table[0],fk[1], fk[2],fk[3])
                    print(f"  Column {fk[1]} references {fk[2]}.{fk[3]}")
    db_instance.close()
    kGraph.saveRDF('constructedKG/{}_{}_{}.ttl'.format(DBServer, DBEngine, DBName))
# print(kGraph.graph.serialize(format='turtle'))

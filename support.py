import yaml

class findDB:
    def __init__(self, configFile) -> None:
        self.configFile = configFile
        
    def loadConfig(self):
        with open(self.configFile, 'r') as file:
            self.data = yaml.safe_load(file)
        return self.data

    def pringParams(self):
        for db in self.data['databases']:
            print(f"Database Server: {db['name']}")
            print(f"Engine: {db['engine']}")
            print(f"Description: {db['description']}")

            connection_details = db.get('connection_details')

            # Check if the connection is file-based or uses host/port details
            if 'database_files' in connection_details:
                print(f"Database Files: {', '.join(connection_details['database_files'])}")
            else:
                print(f"Host: {connection_details.get('host')}")
                print(f"Port: {connection_details.get('port')}")
                print(f"Username: {connection_details.get('username')}")
                print(f"Password: {connection_details.get('password')}")
                print(f"Database: {connection_details.get('database')}")

            print('-' * 40)
        
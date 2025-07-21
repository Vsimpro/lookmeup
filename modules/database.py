import os, sqlite3

# Global Variables
CONNECTION = None


def get_tables() -> list:
    """
    #### Returns 
    * list(): list of the table names in the DB.
    """
    global CONNECTION

    cursor = CONNECTION.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    
    tables = cursor.fetchall()    

    return tables


def create_tables( connection, tables ) -> bool:
    """
    Create all the needed tables required for usage.

    ### Returns
    * bool: True on success, False on any error.
    """
    
    try:
        cursor = connection.cursor()
        
        
        for table_name in tables:
            exists = len( query_database( f"SELECT name FROM sqlite_master WHERE type='table' AND name='{ table_name }';" ))
            if exists == 1:
                print( "[+] Table exists: ", table_name )  
                continue

            cursor.execute( tables[table_name] ); print( "[+] Table: ", table_name, "created" )           

        connection.commit()
        cursor.close()

    except Exception as e:
        print( "[!] Error when creating tables,", e )
        return False
    
    return True


def query_database( query:str, user_input:tuple=None ) -> list:
    """
    Run specified query in the Database.

    Parameters
    * query: the query to be ran agaisnt the DB.
    * user_input: None, or the user specified parameters. 
    
    Returns
    * list(): the results of the query.
    """
    global CONNECTION
    rows = []

    cursor = CONNECTION.cursor()
    
    try:
        
        if user_input:
            cursor.execute(query, user_input)
    
        else:
            cursor.execute(query)

    except Exception as e:
        print( f"[!] [DATABASE] Ran into an issue while running execute({ query }). Details: ", e )
        return False
    
    
    rows = cursor.fetchall()
    return rows
    

def insert_data( query:str, data ) -> bool:
    """
    Insert data into a table using premade queries.

    Returns
    * bool: Upon success
    """
    global CONNECTION

    try:
        cursor = CONNECTION.cursor()
        if type(data) == list:
            cursor.executemany( query, data )
            CONNECTION.commit()

        if type(data) == tuple:
            cursor.execute( query, data )
            CONNECTION.commit()

    except Exception as e:
        CONNECTION.rollback()
        print( f"[!] [DATABASE] Ran into an issue while running execute({ query }), with data {data}, details: ", e )
        return False
    
    return True


def update_data( query:str, data ) -> tuple:
    """
    Update data in a table using premade queries.

    Returns
    * bool: Upon success
    """
    global CONNECTION
 
    try:
        cursor = CONNECTION.cursor()
        if type(data) == tuple:
            cursor.execute( query, data )

        CONNECTION.commit()
        print( f"[?] Rows updated: { cursor.rowcount }" )

    except Exception as e:
        CONNECTION.rollback()
        print( f"[!] [DATABASE] Ran into an issue while running execute({ query }), with data {data}, details: ", e )
        return False
    
    return True


def initialize_db( tables, db_name:str = "database.db" ) -> bool:
    """
    Prepare the Database for use.

    ### Parameters
    * db_name: Name of the SQLite database file.

    ### Returns 
    * bool: Boolean upon success.
    """
    global CONNECTION

    db_exists = None
   
    try:        
        print( "[>] Connecting to database.")

        db_exists = os.path.exists(db_name)
        if not db_exists:
            print("[>] Database file not found, creating new one.")
            with open(db_name, "w+") as file: file.write("")
                
        CONNECTION = sqlite3.connect( db_name, check_same_thread=False )
        print( "[>] Connection made " )
                
        if not create_tables( CONNECTION, tables ):
            return False
        print( "[>] Desired tables made." )

    except Exception as error:
        print(f"Error: {error}")
        return False

    return True
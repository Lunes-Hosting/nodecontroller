import sqlite3
from typing import Optional, Union, Tuple, List, Any


DATABASE = 'information.db'
class DatabaseManager():
    """
    Manages database operations including connections and query execution.
    Designed to be compatible with existing database usage patterns.
    """
    
    @classmethod
    def get_connection(cls, database: str = DATABASE) -> Tuple[sqlite3.Connection, sqlite3.Cursor]:
        """
        Creates and returns a database connection with standard configuration.
        
        Args:
            database: Database file path to connect to
            
        Returns:
            tuple: (connection, cursor)
        """
        connection = sqlite3.connect(database)
        connection.row_factory = sqlite3.Row  # ✅ This enables dictionary-like rows
        cursor = connection.cursor()
        return connection, cursor

    @classmethod
    def execute_query(
        cls,
        query: str,
        values: Optional[tuple] = None,
        database: str = DATABASE,
        fetch_all: bool = False
    ) -> Optional[Union[Tuple, List[Tuple]]]:
        """
        Executes a database query. For SELECT queries returns results, otherwise returns None.
        
        Args:
            query: SQL query to execute
            values: Query parameter values
            database: Target database file path
            fetch_all: Whether to return all results for SELECT queries
            
        Returns:
            tuple: First row for SELECT queries when fetch_all=False
            list[tuple]: All rows for SELECT queries when fetch_all=True
            None: For non-SELECT queries
            
        Raises:
            Exception: If database error occurs
        """
        connection = None
        cursor = None
        try:
            connection, cursor = cls.get_connection(database)
            
            if values:
                cursor.execute(query, values)
            else:
                cursor.execute(query)
                
            if query.strip().upper().startswith('SELECT'):
                if fetch_all:
                    result = cursor.fetchall()
                else:
                    result = cursor.fetchone()
                return result
                
            connection.commit()
            return None
            
        except Exception as e:
            if connection:
                connection.rollback()
            print(f"Database error: {e}")
            raise
            
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
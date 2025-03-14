"""
Oracle database connection and utilities.
"""
import logging
import json
from typing import List, Dict, Any, Optional, Tuple, Union
import cx_Oracle

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class OracleDB:
    """
    Oracle database connection and utility class.
    """
    def __init__(self):
        """Initialize the Oracle database connection."""
        self.connection = None
        self.cursor = None
        self.dsn = cx_Oracle.makedsn(
            host=settings.ORACLE_HOST,
            port=settings.ORACLE_PORT,
            service_name=settings.ORACLE_SERVICE
        )
        
    def connect(self) -> None:
        """Connect to the Oracle database."""
        try:
            self.connection = cx_Oracle.connect(
                user=settings.ORACLE_USER,
                password=settings.ORACLE_PASSWORD,
                dsn=self.dsn
            )
            self.cursor = self.connection.cursor()
            logger.info("Connected to Oracle database")
        except cx_Oracle.Error as error:
            logger.error(f"Error connecting to Oracle database: {error}")
            raise
    
    def disconnect(self) -> None:
        """Disconnect from the Oracle database."""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            logger.info("Disconnected from Oracle database")
        except cx_Oracle.Error as error:
            logger.error(f"Error disconnecting from Oracle database: {error}")
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a query and return the results as a list of dictionaries.
        
        Args:
            query: The SQL query to execute.
            params: Optional dictionary of parameters for the query.
            
        Returns:
            List of dictionaries with the query results.
        """
        if not self.connection or not self.cursor:
            self.connect()
            
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
                
            # Get column names
            columns = [col[0].lower() for col in self.cursor.description]
            
            # Return results as a list of dictionaries
            results = []
            for row in self.cursor:
                results.append(dict(zip(columns, row)))
            
            return results
        except cx_Oracle.Error as error:
            logger.error(f"Error executing query: {error}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Params: {params}")
            raise
            
    def execute_update(self, query: str, params: Optional[Dict[str, Any]] = None) -> int:
        """
        Execute an update query and return the number of rows affected.
        
        Args:
            query: The SQL query to execute.
            params: Optional dictionary of parameters for the query.
            
        Returns:
            Number of rows affected.
        """
        if not self.connection or not self.cursor:
            self.connect()
            
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
                
            self.connection.commit()
            return self.cursor.rowcount
        except cx_Oracle.Error as error:
            if self.connection:
                self.connection.rollback()
            logger.error(f"Error executing update: {error}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Params: {params}")
            raise
            
    def fetch_batch(self, query: str, params: Optional[Dict[str, Any]] = None, batch_size: int = 1000) -> List[Dict[str, Any]]:
        """
        Fetch data in batches to avoid memory issues with large results.
        
        Args:
            query: The SQL query to execute.
            params: Optional dictionary of parameters for the query.
            batch_size: Number of records to fetch at a time.
            
        Returns:
            List of dictionaries with the query results.
        """
        if not self.connection or not self.cursor:
            self.connect()
            
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
                
            # Get column names
            columns = [col[0].lower() for col in self.cursor.description]
            
            # Fetch and yield batches
            batch = self.cursor.fetchmany(batch_size)
            while batch:
                results = [dict(zip(columns, row)) for row in batch]
                yield results
                batch = self.cursor.fetchmany(batch_size)
                
        except cx_Oracle.Error as error:
            logger.error(f"Error fetching batch: {error}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Params: {params}")
            raise
            
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


# Instantiate a single instance to be reused
oracle_db = OracleDB() 
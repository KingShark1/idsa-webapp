import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def test_connection(connection_string):
    try:
        # Create the SQLAlchemy engine
        engine = create_engine(connection_string)

        # Try to connect and execute a simple query
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("Connection successful!")
            print("Test query result:", result.scalar())

        # If we get here, the connection was successful
        return True

    except SQLAlchemyError as e:
        print("Error connecting to the database:")
        print(str(e))
        return False

if __name__ == "__main__":
    connection_string = 'postgresql://postgres:ErmWsGnksaBwaCWStClxMdAhUTAFILmP@autorack.proxy.rlwy.net:47961/railway'

    if test_connection(connection_string):
        print("Database connection test passed.")
        sys.exit(0)
    else:
        print("Database connection test failed.")
        sys.exit(1)

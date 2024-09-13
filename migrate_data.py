from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker
from models import Base

def migrate_data():
    engine_lite = create_engine('sqlite:///swimming_competition.db')
    engine_cloud = create_engine('postgresql://postgres:ErmWsGnksaBwaCWStClxMdAhUTAFILmP@autorack.proxy.rlwy.net:47961/railway')

    Session_lite = sessionmaker(bind=engine_lite)
    Session_cloud = sessionmaker(bind=engine_cloud)

    session_lite = Session_lite()
    session_cloud = Session_cloud()

    try:
        for table in Base.metadata.sorted_tables:
            # Clear existing data in the destination table
            session_cloud.execute(text(f"TRUNCATE TABLE {table.name} RESTART IDENTITY CASCADE"))

            # Fetch data from SQLite
            stmt = select(table)
            rows = session_lite.execute(stmt).fetchall()

            if rows:
                # Convert rows to list of dictionaries
                data = [dict(row._mapping) for row in rows]

                # Insert data into PostgreSQL
                session_cloud.execute(table.insert().values(data))

        session_cloud.commit()
        print("Data migration completed successfully.")

    except Exception as e:
        session_cloud.rollback()
        print(f"An error occurred: {str(e)}")

    finally:
        session_lite.close()
        session_cloud.close()

if __name__ == "__main__":
    migrate_data()

import mysql.connector
import json
from datetime import datetime, date

def export_database_to_json():
    print("Enter MySQL connection details:")
    host = input("Host (default: localhost): ").strip() or 'localhost'
    user = input("Username (default: root): ").strip() or 'root'
    password = input("Password (leave empty if no password): ").strip()
    database_name = input("Database name to export: ").strip()
    
    if not database_name:
        print("Error: Database name cannot be empty!")
        return
    
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database_name
        )
        
        cursor = connection.cursor()
        
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        
        print(f"Found {len(tables)} tables: {tables}")
        
        database_json = {
            "database": database_name,
            "exported_at": datetime.now().isoformat(),
            "table_count": len(tables),
            "tables": {}
        }
        
        for table_name in tables:
            print(f"Exporting table: {table_name}")
            
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = [col[0] for col in cursor.fetchall()]
            
            cursor.execute(f"SELECT * FROM `{table_name}`")
            rows = cursor.fetchall()

            table_data = []
            for row in rows:
                row_dict = {}
                for i, value in enumerate(row):
                    if isinstance(value, (datetime, date)):
                        row_dict[columns[i]] = value.isoformat() if value is not None else None
                    elif value is None:
                        row_dict[columns[i]] = None
                    elif isinstance(value, bytes):
                        row_dict[columns[i]] = value.decode('utf-8', errors='ignore')
                    elif isinstance(value, (int, float, str, bool)):
                        row_dict[columns[i]] = value
                    else:
                        row_dict[columns[i]] = str(value)
                table_data.append(row_dict)
            
            database_json["tables"][table_name] = {
                "columns": columns,
                "row_count": len(table_data),
                "data": table_data
            }
        
        output_file = f'c:\\Users\\Caltech\\Downloads\\sql\\{database_name}_database.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(database_json, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"Database exported successfully to {output_file}")
        print(f"Total tables exported: {len(tables)}")
        
        total_rows = sum(len(table_info["data"]) for table_info in database_json["tables"].values())
        print(f"Total rows exported: {total_rows}")
        
    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
    except Exception as err:
        print(f"General Error: {err}")
    finally:
        try:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
                print("MySQL connection closed.")
        except Exception as e:
            print(f"Error closing connection: {e}")

if __name__ == "__main__":
    export_database_to_json()
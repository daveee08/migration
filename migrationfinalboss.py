import mysql.connector
import json
import os
import sys
import time
from datetime import datetime, date
from tkinter import filedialog, messagebox
import tkinter as tk

def format_file_size(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    size = float(size_bytes)
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    return f"{size:.1f} {size_names[i]}"

def show_progress_bar(current, total, prefix="", suffix="", length=30):
    """Display a download-style progress bar"""
    percent = (current / total) * 100
    filled_length = int(length * current // total)
    bar = '█' * filled_length + '░' * (length - filled_length)
    print(f'\r{prefix} [{bar}] {percent:.1f}% {suffix}', end='', flush=True)

def select_tables_to_export(all_tables):
    """Allow user to select which tables to export"""
    print(f"\nFound {len(all_tables)} tables in the database:")
    
    for i, table in enumerate(all_tables, 1):
        print(f"{i:2d}. {table}")
    
    print("\nTable Selection Options:")
    print("1. Export ALL tables")
    print("2. Select specific tables by numbers (e.g., 1,3,5-8)")
    print("3. Select tables by name patterns (e.g., student*,grade*)")
    
    choice = input("\nChoose option (1, 2, or 3): ").strip()
    
    if choice == "1":
        return all_tables
    
    elif choice == "2":
        while True:
            try:
                selection = input("\nEnter table numbers (e.g., 1,3,5-8): ").strip()
                selected_tables = []
                
                parts = selection.split(',')
                for part in parts:
                    part = part.strip()
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        for i in range(start, end + 1):
                            if 1 <= i <= len(all_tables):
                                selected_tables.append(all_tables[i-1])
                    else:
                        i = int(part)
                        if 1 <= i <= len(all_tables):
                            selected_tables.append(all_tables[i-1])
                
                if selected_tables:
                    print(f"Selected {len(selected_tables)} tables: {selected_tables}")
                    confirm = input("Proceed with these tables? (y/n): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        return list(set(selected_tables))
                else:
                    print("No valid tables selected.")
                    
            except ValueError:
                print("Invalid input. Please use format like: 1,3,5-8")
    
    elif choice == "3":
        patterns = input("\nEnter patterns separated by commas (e.g., student*,grade*): ").strip()
        selected_tables = []
        
        for pattern in patterns.split(','):
            pattern = pattern.strip().lower()
            if pattern.endswith('*'):
                prefix = pattern[:-1]
                matching = [table for table in all_tables if table.lower().startswith(prefix)]
                selected_tables.extend(matching)
            else:
                matching = [table for table in all_tables if pattern in table.lower()]
                selected_tables.extend(matching)
        
        if selected_tables:
            selected_tables = list(set(selected_tables))
            print(f"Selected {len(selected_tables)} tables: {selected_tables}")
            confirm = input("Proceed with these tables? (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                return selected_tables
        else:
            print("No tables matched your patterns.")
    
    print("Invalid selection or cancelled. Exporting all tables by default.")
    return all_tables

def select_export_format():
    """Allow user to choose export format"""
    print("\nExport Format Options:")
    print("1. Single JSON file (all tables combined)")
    print("2. Separate JSON files (one file per table)")
    
    while True:
        choice = input("\nChoose export format (1 or 2): ").strip()
        if choice in ['1', '2']:
            return choice
        print("Invalid choice. Please enter 1 or 2.")

def select_output_location():
    """Allow user to choose output location using GUI dialog or manual input"""
    print("\nOutput Location Options:")
    print("1. Current directory (default)")
    print("2. Browse for directory (GUI)")
    print("3. Enter path manually")
    
    while True:
        choice = input("\nChoose output location (1, 2, or 3): ").strip()
        
        if choice == "1":
            # Use current directory
            output_dir = os.getcwd()
            print(f"Files will be saved to: {output_dir}")
            return output_dir
            
        elif choice == "2":
            # GUI file browser
            print("Opening directory browser...")
            
            try:
                # Create a root window and hide it
                root = tk.Tk()
                root.withdraw()  # Hide the main window
                root.lift()  # Bring to front on macOS
                root.attributes('-topmost', True)  # Stay on top
                
                # Show directory selection dialog
                output_dir = filedialog.askdirectory(
                    title="Select Download Directory - MySQL to JSON Export",
                    initialdir=os.getcwd(),
                    mustexist=False
                )
                
                root.destroy()  # Clean up
                
                if output_dir:
                    print(f"Selected directory: {output_dir}")
                    return output_dir
                else:
                    print("No directory selected. Please try again.")
                    continue
                    
            except Exception as e:
                print(f"GUI dialog error: {e}")
                print("Falling back to manual input...")
                choice = "3"  # Fall back to manual input
                
        if choice == "3":
            # Manual directory input
            while True:
                custom_path = input("\nEnter the full path for download directory: ").strip()
                
                if not custom_path:
                    print("Path cannot be empty.")
                    continue
                
                # Expand user path (~ on Unix systems)
                custom_path = os.path.expanduser(custom_path)
                
                # Check if directory exists
                if os.path.exists(custom_path):
                    if os.path.isdir(custom_path):
                        print(f"Files will be saved to: {custom_path}")
                        return custom_path
                    else:
                        print("Error: Path exists but is not a directory.")
                        continue
                else:
                    # Ask if user wants to create the directory
                    create = input(f"Directory '{custom_path}' does not exist. Create it? (y/n): ").strip().lower()
                    if create in ['y', 'yes']:
                        try:
                            os.makedirs(custom_path, exist_ok=True)
                            print(f"Directory created: {custom_path}")
                            return custom_path
                        except Exception as e:
                            print(f"Error creating directory: {e}")
                            continue
                    else:
                        print("Please enter a different path.")
                        continue
        
        if choice not in ["1", "2", "3"]:
            print("Invalid choice. Please enter 1, 2, or 3.")

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
        all_tables = [table[0] for table in cursor.fetchall()]
        
        # Let user select which tables to export
        selected_tables = select_tables_to_export(all_tables)
        
        # Let user select export format
        export_format = select_export_format()
        
        # Let user select output location
        output_dir = select_output_location()
        
        # Prepare metadata
        export_metadata = {
            "database": database_name,
            "exported_at": datetime.now().isoformat(),
            "total_tables_in_db": len(all_tables),
            "selected_tables_count": len(selected_tables),
            "export_format": "single_file" if export_format == "1" else "separate_files",
            "output_location": output_dir
        }
        
        if export_format == "1":
            # Single file export
            database_json = export_metadata.copy()
            database_json["tables"] = {}
        
        exported_files = []
        total_tables = len(selected_tables)
        
        print(f"\nStarting export of {total_tables} tables...")
        print("=" * 60)
        
        for table_index, table_name in enumerate(selected_tables, 1):
            print(f"\nProcessing table: {table_name} ({table_index}/{total_tables})")
            
            # Get table info first
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            row_count = cursor.fetchone()[0]
            
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = [col[0] for col in cursor.fetchall()]
            
            print(f"   Columns: {len(columns)} | Rows: {row_count:,}")
            
            # Fetch data with progress simulation
            print(f"   Downloading data...", end="")
            cursor.execute(f"SELECT * FROM `{table_name}`")
            
            # Simulate download progress
            for i in range(11):
                show_progress_bar(i, 10, "   ", f"fetching rows...")
                time.sleep(0.1)  # Simulate processing time
            print()  # New line after progress bar
            
            rows = cursor.fetchall()
            print(f"   Fetched {len(rows):,} rows successfully")

            # Convert data with progress bar
            print(f"   Converting data to JSON format...")
            table_data = []
            total_rows = len(rows)
            
            for row_index, row in enumerate(rows):
                if total_rows > 1000 and row_index % max(1, total_rows // 20) == 0:
                    show_progress_bar(row_index, total_rows, "   ", f"processing {row_index:,}/{total_rows:,} rows")
                
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
            
            if total_rows > 1000:
                show_progress_bar(total_rows, total_rows, "   ", f"completed {total_rows:,} rows")
                print()  # New line after progress bar
            
            table_json = {
                "table_name": table_name,
                "database": database_name,
                "exported_at": export_metadata["exported_at"],
                "columns": columns,
                "row_count": len(table_data),
                "data": table_data
            }
            
            if export_format == "1":
                # Single file: add to main JSON
                database_json["tables"][table_name] = {
                    "columns": columns,
                    "row_count": len(table_data),
                    "data": table_data
                }
            else:
                # Separate files: create individual JSON file
                table_file = os.path.join(output_dir, f'{database_name}_{table_name}.json')
                
                print(f"   Saving to file...")
                # Simulate file writing progress
                for i in range(6):
                    show_progress_bar(i, 5, "   ", f"writing JSON...")
                    time.sleep(0.05)
                
                with open(table_file, 'w', encoding='utf-8') as f:
                    json.dump(table_json, f, indent=2, ensure_ascii=False, default=str)
                
                # Get file size
                file_size = os.path.getsize(table_file)
                show_progress_bar(5, 5, "   ", f"complete")
                print()  # New line after progress bar
                
                exported_files.append(table_file)
                print(f"   Saved: {os.path.basename(table_file)} ({format_file_size(file_size)})")
                print(f"   Location: {table_file}")
                
                # Add separator between tables
                if table_index < total_tables:
                    print("   " + "-" * 50)
        
        # Handle final output based on format
        print(f"\nFinalizing export...")
        
        if export_format == "1":
            # Single file export
            output_file = os.path.join(output_dir, f'{database_name}_database.json')
            
            print(f"   Creating combined JSON file...")
            for i in range(11):
                show_progress_bar(i, 10, "   ", f"compiling data...")
                time.sleep(0.1)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(database_json, f, indent=2, ensure_ascii=False, default=str)
            
            file_size = os.path.getsize(output_file)
            show_progress_bar(10, 10, "   ", f"complete")
            print()
            
            print(f"\nDOWNLOAD COMPLETE!")
            print("=" * 60)
            print(f"Database: {database_name}")
            print(f"File: {os.path.basename(output_file)}")
            print(f"Size: {format_file_size(file_size)}")
            print(f"Location: {output_file}")
            
            total_rows = sum(len(table_info["data"]) for table_info in database_json["tables"].values())
            
        else:
            # Multiple files export - Create summary file
            summary_file = os.path.join(output_dir, f'{database_name}_export_summary.json')
            summary_data = export_metadata.copy()
            summary_data["exported_files"] = exported_files
            summary_data["table_list"] = selected_tables
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Calculate total file size
            total_size = sum(os.path.getsize(f) for f in exported_files)
            summary_size = os.path.getsize(summary_file)
            
            print(f"\nDOWNLOAD COMPLETE!")
            print("=" * 60)
            print(f"Database: {database_name}")
            print(f"Files: {len(exported_files)} table files + 1 summary")
            print(f"Total Size: {format_file_size(total_size + summary_size)}")
            print(f"Location: {output_dir}")
            print(f"Summary: {os.path.basename(summary_file)}")
            
            total_rows = sum(len(json.load(open(f))["data"]) for f in exported_files)
        
        print(f"\nEXPORT STATISTICS:")
        print(f"   Tables in database: {len(all_tables)}")
        print(f"   Tables exported: {len(selected_tables)}")
        print(f"   Total rows exported: {total_rows:,}")
        print(f"   Export completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
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
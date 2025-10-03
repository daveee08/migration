# MySQL to JSON Database Exporter

A powerful and user-friendly Python tool to export MySQL databases to JSON format with download-style progress tracking and GUI directory selection.

## Features

- **Flexible Table Selection**
  - Export all tables or select specific ones
  - Select by table numbers (e.g., `1,3,5-8`)
  - Select by name patterns with wildcards (e.g., `student*`, `grade*`)

- **Multiple Export Formats**
  - Single JSON file (all tables combined)
  - Separate JSON files (one per table)
  - Summary file with export metadata

- **GUI Directory Browser**
  - Native file dialog (like browser downloads)
  - Manual path entry option
  - Auto-create directories if needed

- **Download-Style Progress**
  - Real-time progress bars
  - File size reporting
  - Processing statistics
  - Professional completion summary

- **User-Friendly Interface**
  - Interactive prompts for all options
  - Connection parameter input
  - Error handling and validation
  - Clean, professional output

## Requirements

- Python 3.6 or higher
- MySQL server (local or remote)
- `mysql-connector-python` package (only external dependency)

**Note:** This tool uses only built-in Python libraries except for the MySQL connector, so it can run with minimal setup.

## Installation

### Option 1: Quick Setup (Global Installation)

1. **Download the script**
   - Download `migrationfinalboss.py` and `requirements.txt`
   - Place them in your desired folder

2. **Install the dependency**
   ```bash
   pip install mysql-connector-python
   ```

3. **Run the script**
   ```bash
   python migrationfinalboss.py
   ```

### Option 2: Full Project Setup (With Virtual Environment - Recommended)

1. **Clone or download this repository**
   ```bash
   git clone https://github.com/yourusername/mysql-json-exporter.git
   cd mysql-json-exporter
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   
   # On Windows
   .venv\Scripts\activate
   
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

Run the script:
```bash
python migrationfinalboss.py
```

### Step-by-Step Process

1. **Enter MySQL Connection Details**
   ```
   Enter MySQL connection details:
   Host (default: localhost): 
   Username (default: root): 
   Password (leave empty if no password): 
   Database name to export: your_database_name
   ```

2. **Select Tables to Export**
   ```
   Found 53 tables in the database:
    1. users
    2. orders
    3. products
   ...
   
   Table Selection Options:
   1. Export ALL tables
   2. Select specific tables by numbers (e.g., 1,3,5-8)
   3. Select tables by name patterns (e.g., user*,order*)
   ```

3. **Choose Export Format**
   ```
   Export Format Options:
   1. Single JSON file (all tables combined)
   2. Separate JSON files (one file per table)
   ```

4. **Select Output Location**
   ```
   Output Location Options:
   1. Current directory (default)
   2. Browse for directory (GUI)
   3. Enter path manually
   ```

5. **Watch the Export Progress**
   ```
   Starting export of 5 tables...
   ============================================================
   
   Processing table: users (1/5)
      Columns: 8 | Rows: 1,250
      Downloading data... [██████████] 100.0% fetching rows...
      Fetched 1,250 rows successfully
      Converting data to JSON format...
      Saving to file...
      [██████████] 100.0% complete
      Saved: mydb_users.json (456.7 KB)
      Location: C:\MyExports\mydb_users.json
   ```

## Output Examples

### Single File Export
```json
{
  "database": "mydb",
  "exported_at": "2025-10-03T15:30:45.123456",
  "total_tables_in_db": 53,
  "selected_tables_count": 5,
  "export_format": "single_file",
  "tables": {
    "users": {
      "columns": ["id", "name", "email", "created_at"],
      "row_count": 1250,
      "data": [
        {
          "id": 1,
          "name": "John Doe",
          "email": "john@example.com",
          "created_at": "2024-01-15T10:30:00"
        }
      ]
    }
  }
}
```

### Separate Files Export
Each table gets its own file:
- `mydb_users.json`
- `mydb_orders.json`
- `mydb_products.json`
- `mydb_export_summary.json` (contains metadata and file list)

## Configuration

### Connection Parameters
- **Host**: MySQL server hostname or IP
- **Username**: MySQL username
- **Password**: MySQL password (can be empty)
- **Database**: Name of database to export

### Table Selection Patterns
- **All tables**: Choose option 1
- **By numbers**: `1,3,5` or `1-5,8,10-12`
- **By patterns**: `user*,order*` (supports wildcards)

### Export Formats
- **Single file**: All tables in one JSON file
- **Separate files**: Individual JSON file per table + summary

## File Structure

```
your-export-folder/
├── database_name_table1.json
├── database_name_table2.json
├── database_name_table3.json
└── database_name_export_summary.json
```

## Error Handling

The tool includes comprehensive error handling for:
- MySQL connection issues
- Invalid table selections
- File system permissions
- GUI dialog failures (falls back to manual input)
- Large dataset processing

## Performance Notes

- **Large tables**: Progress bars show real-time conversion progress
- **Memory usage**: Data is processed table by table to manage memory
- **File sizes**: Automatic file size reporting in human-readable format
- **Speed**: Optimized JSON serialization with proper encoding

## Troubleshooting

### Common Issues

1. **MySQL Connection Error**
   ```
   MySQL Error: (2003, "Can't connect to MySQL server...")
   ```
   - Verify MySQL server is running
   - Check host, username, and password
   - Ensure database exists

2. **GUI Dialog Not Working**
   ```
   GUI dialog error: ...
   Falling back to manual input...
   ```
   - The tool automatically falls back to manual path entry
   - This is normal on some Linux systems without GUI

3. **Permission Denied**
   ```
   Error creating directory: [Errno 13] Permission denied
   ```
   - Choose a different output directory
   - Run with appropriate permissions
   - Check disk space

### Performance Tips

- For very large databases, consider exporting tables in batches
- Use separate files format for easier processing of individual tables
- Monitor disk space before exporting large datasets

## License

This project is open source and available under the [MIT License](LICENSE).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

If you encounter any issues or have questions:
1. Check the troubleshooting section above
2. Open an issue on GitHub
3. Provide MySQL version, Python version, and error details

## Changelog

### Version 1.0.0
- Initial release
- MySQL database export to JSON
- GUI directory selection
- Progress tracking
- Multiple export formats
- Table selection options
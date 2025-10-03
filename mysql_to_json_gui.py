import sys
import mysql.connector
import json
import os
import time
from datetime import datetime, date
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QProgressBar, QCheckBox, QListWidget,
                             QFileDialog, QMessageBox, QTabWidget, QGridLayout,
                             QGroupBox, QRadioButton, QButtonGroup, QScrollArea,
                             QFrame, QSplitter)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap, QPalette, QColor

class DatabaseExportThread(QThread):
    progress_signal = pyqtSignal(int, str)
    table_progress_signal = pyqtSignal(str, int, int)
    finished_signal = pyqtSignal(bool, str)
    log_signal = pyqtSignal(str)
    
    def __init__(self, connection_params, selected_tables, export_format, output_dir):
        super().__init__()
        self.connection_params = connection_params
        self.selected_tables = selected_tables
        self.export_format = export_format
        self.output_dir = output_dir
        self.is_cancelled = False
    
    def cancel_export(self):
        self.is_cancelled = True
    
    def format_file_size(self, size_bytes):
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(size_bytes)
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        return f"{size:.1f} {size_names[i]}"
    
    def run(self):
        try:
            self.log_signal.emit("Connecting to MySQL database...")
            connection = mysql.connector.connect(**self.connection_params)
            cursor = connection.cursor()
            
            total_tables = len(self.selected_tables)
            exported_files = []
            

            export_metadata = {
                "database": self.connection_params['database'],
                "exported_at": datetime.now().isoformat(),
                "selected_tables_count": total_tables,
                "export_format": "single_file" if self.export_format == "single" else "separate_files",
                "output_location": self.output_dir
            }
            
            if self.export_format == "single":
                database_json = export_metadata.copy()
                database_json["tables"] = {}
            
            for table_index, table_name in enumerate(self.selected_tables, 1):
                if self.is_cancelled:
                    break
                
                self.table_progress_signal.emit(table_name, table_index, total_tables)
                self.log_signal.emit(f"Processing table: {table_name} ({table_index}/{total_tables})")
                

                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                row_count = cursor.fetchone()[0]
                
                cursor.execute(f"DESCRIBE `{table_name}`")
                columns = [col[0] for col in cursor.fetchall()]
                
                self.log_signal.emit(f"   Columns: {len(columns)} | Rows: {row_count:,}")
                

                self.log_signal.emit("   Fetching data...")
                cursor.execute(f"SELECT * FROM `{table_name}`")
                rows = cursor.fetchall()
                

                self.log_signal.emit("   Converting to JSON format...")
                table_data = []
                total_rows = len(rows)
                
                for row_index, row in enumerate(rows):
                    if self.is_cancelled:
                        break
                    

                    if total_rows > 1000 and row_index % max(1, total_rows // 20) == 0:
                        progress = int((row_index / total_rows) * 100)
                        self.progress_signal.emit(progress, f"Converting {table_name}: {row_index:,}/{total_rows:,} rows")
                    
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
                
                if self.is_cancelled:
                    break
                

                table_json = {
                    "table_name": table_name,
                    "database": self.connection_params['database'],
                    "exported_at": export_metadata["exported_at"],
                    "columns": columns,
                    "row_count": len(table_data),
                    "data": table_data
                }
                
                if self.export_format == "single":
                    database_json["tables"][table_name] = {
                        "columns": columns,
                        "row_count": len(table_data),
                        "data": table_data
                    }
                else:

                    table_file = os.path.join(self.output_dir, f'{self.connection_params["database"]}_{table_name}.json')
                    self.log_signal.emit(f"   Saving to: {os.path.basename(table_file)}")
                    
                    with open(table_file, 'w', encoding='utf-8') as f:
                        json.dump(table_json, f, indent=2, ensure_ascii=False, default=str)
                    
                    file_size = os.path.getsize(table_file)
                    exported_files.append(table_file)
                    self.log_signal.emit(f"   Saved: {os.path.basename(table_file)} ({self.format_file_size(file_size)})")
                

                overall_progress = int((table_index / total_tables) * 100)
                self.progress_signal.emit(overall_progress, f"Completed {table_index}/{total_tables} tables")
            
            if not self.is_cancelled:

                if self.export_format == "single":
                    output_file = os.path.join(self.output_dir, f'{self.connection_params["database"]}_database.json')
                    self.log_signal.emit(f"Creating combined file: {os.path.basename(output_file)}")
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(database_json, f, indent=2, ensure_ascii=False, default=str)
                    
                    file_size = os.path.getsize(output_file)
                    self.finished_signal.emit(True, f"Export completed successfully!\nFile: {output_file}\nSize: {self.format_file_size(file_size)}")
                else:

                    summary_file = os.path.join(self.output_dir, f'{self.connection_params["database"]}_export_summary.json')
                    summary_data = export_metadata.copy()
                    summary_data["exported_files"] = exported_files
                    summary_data["table_list"] = self.selected_tables
                    
                    with open(summary_file, 'w', encoding='utf-8') as f:
                        json.dump(summary_data, f, indent=2, ensure_ascii=False, default=str)
                    
                    total_size = sum(os.path.getsize(f) for f in exported_files)
                    self.finished_signal.emit(True, f"Export completed successfully!\nFiles: {len(exported_files)} tables + summary\nLocation: {self.output_dir}\nTotal Size: {self.format_file_size(total_size)}")
            else:
                self.finished_signal.emit(False, "Export cancelled by user")
            
            cursor.close()
            connection.close()
            
        except mysql.connector.Error as err:
            self.finished_signal.emit(False, f"MySQL Error: {err}")
        except Exception as err:
            self.finished_signal.emit(False, f"Error: {err}")

class MySQLtoJSONGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.export_thread = None
        self.all_tables = []
        self.connection = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("MySQL to JSON Database Exporter")
        self.setGeometry(100, 100, 900, 700)
        

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        

        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        

        self.create_connection_tab()
        

        self.create_tables_tab()
        

        self.create_export_tab()
        

        self.create_progress_tab()
        

        self.statusBar().showMessage("Ready to connect to MySQL database")
    
    def create_connection_tab(self):
        connection_tab = QWidget()
        self.tab_widget.addTab(connection_tab, "1. Connection")
        
        layout = QVBoxLayout(connection_tab)
        

        connection_group = QGroupBox("MySQL Connection Settings")
        connection_layout = QGridLayout(connection_group)
        

        self.host_input = QLineEdit("localhost")
        self.user_input = QLineEdit("root")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.database_input = QLineEdit()
        
        connection_layout.addWidget(QLabel("Host:"), 0, 0)
        connection_layout.addWidget(self.host_input, 0, 1)
        connection_layout.addWidget(QLabel("Username:"), 1, 0)
        connection_layout.addWidget(self.user_input, 1, 1)
        connection_layout.addWidget(QLabel("Password:"), 2, 0)
        connection_layout.addWidget(self.password_input, 2, 1)
        connection_layout.addWidget(QLabel("Database:"), 3, 0)
        connection_layout.addWidget(self.database_input, 3, 1)
        

        self.test_connection_btn = QPushButton("Test Connection")
        self.test_connection_btn.clicked.connect(self.test_connection)
        connection_layout.addWidget(self.test_connection_btn, 4, 0, 1, 2)
        

        self.connection_status = QLabel("Not connected")
        self.connection_status.setStyleSheet("color: red;")
        connection_layout.addWidget(self.connection_status, 5, 0, 1, 2)
        
        layout.addWidget(connection_group)
        layout.addStretch()
    
    def create_tables_tab(self):
        tables_tab = QWidget()
        self.tab_widget.addTab(tables_tab, "2. Tables")
        
        layout = QVBoxLayout(tables_tab)
        

        tables_group = QGroupBox("Table Selection")
        tables_layout = QVBoxLayout(tables_group)
        

        selection_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.select_none_btn = QPushButton("Select None")
        self.refresh_tables_btn = QPushButton("Refresh Tables")
        
        self.select_all_btn.clicked.connect(self.select_all_tables)
        self.select_none_btn.clicked.connect(self.select_no_tables)
        self.refresh_tables_btn.clicked.connect(self.load_tables)
        
        selection_layout.addWidget(self.select_all_btn)
        selection_layout.addWidget(self.select_none_btn)
        selection_layout.addWidget(self.refresh_tables_btn)
        selection_layout.addStretch()
        
        tables_layout.addLayout(selection_layout)
        

        self.tables_list = QListWidget()
        self.tables_list.setSelectionMode(QListWidget.MultiSelection)
        tables_layout.addWidget(self.tables_list)
        

        self.selected_count_label = QLabel("No tables selected")
        tables_layout.addWidget(self.selected_count_label)
        
        layout.addWidget(tables_group)
        

        self.tables_list.itemSelectionChanged.connect(self.update_selected_count)
    
    def create_export_tab(self):
        export_tab = QWidget()
        self.tab_widget.addTab(export_tab, "3. Export Options")
        
        layout = QVBoxLayout(export_tab)
        

        format_group = QGroupBox("Export Format")
        format_layout = QVBoxLayout(format_group)
        
        self.format_button_group = QButtonGroup()
        self.single_file_radio = QRadioButton("Single JSON file (all tables combined)")
        self.separate_files_radio = QRadioButton("Separate JSON files (one per table)")
        self.single_file_radio.setChecked(True)
        
        self.format_button_group.addButton(self.single_file_radio)
        self.format_button_group.addButton(self.separate_files_radio)
        
        format_layout.addWidget(self.single_file_radio)
        format_layout.addWidget(self.separate_files_radio)
        
        layout.addWidget(format_group)
        

        output_group = QGroupBox("Output Directory")
        output_layout = QHBoxLayout(output_group)
        
        self.output_dir_input = QLineEdit(os.getcwd())
        self.browse_dir_btn = QPushButton("Browse...")
        self.browse_dir_btn.clicked.connect(self.browse_output_directory)
        
        output_layout.addWidget(self.output_dir_input)
        output_layout.addWidget(self.browse_dir_btn)
        
        layout.addWidget(output_group)
        

        self.start_export_btn = QPushButton("Start Export")
        self.start_export_btn.clicked.connect(self.start_export)
        self.start_export_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }")
        self.start_export_btn.setEnabled(False)
        
        layout.addWidget(self.start_export_btn)
        layout.addStretch()
    
    def create_progress_tab(self):
        progress_tab = QWidget()
        self.tab_widget.addTab(progress_tab, "4. Progress")
        
        layout = QVBoxLayout(progress_tab)
        

        progress_group = QGroupBox("Export Progress")
        progress_layout = QVBoxLayout(progress_group)
        

        self.overall_progress = QProgressBar()
        self.overall_progress_label = QLabel("Ready to start export")
        progress_layout.addWidget(QLabel("Overall Progress:"))
        progress_layout.addWidget(self.overall_progress)
        progress_layout.addWidget(self.overall_progress_label)
        

        self.table_progress_label = QLabel("No table being processed")
        progress_layout.addWidget(self.table_progress_label)
        

        self.cancel_btn = QPushButton("Cancel Export")
        self.cancel_btn.clicked.connect(self.cancel_export)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 10px; }")
        progress_layout.addWidget(self.cancel_btn)
        
        layout.addWidget(progress_group)
        

        log_group = QGroupBox("Export Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)
        

        self.clear_log_btn = QPushButton("Clear Log")
        self.clear_log_btn.clicked.connect(self.clear_log)
        log_layout.addWidget(self.clear_log_btn)
        
        layout.addWidget(log_group)
    
    def test_connection(self):
        try:
            connection_params = {
                'host': self.host_input.text() or 'localhost',
                'user': self.user_input.text() or 'root',
                'password': self.password_input.text(),
                'database': self.database_input.text()
            }
            
            if not connection_params['database']:
                QMessageBox.warning(self, "Warning", "Please enter a database name")
                return
            
            self.connection = mysql.connector.connect(**connection_params)
            self.connection_status.setText("Connected successfully!")
            self.connection_status.setStyleSheet("color: green;")
            

            self.load_tables()
            

            self.tab_widget.setTabEnabled(1, True)
            self.tab_widget.setCurrentIndex(1)
            
            self.statusBar().showMessage("Connected to database successfully")
            
        except mysql.connector.Error as err:
            self.connection_status.setText(f"Connection failed: {err}")
            self.connection_status.setStyleSheet("color: red;")
            QMessageBox.critical(self, "Connection Error", f"Failed to connect to database:\n{err}")
    
    def load_tables(self):
        if not self.connection:
            return
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            cursor.close()
            
            self.all_tables = tables
            self.tables_list.clear()
            
            for table in tables:
                self.tables_list.addItem(table)
            
            self.update_selected_count()
            

            if tables:
                self.tab_widget.setTabEnabled(2, True)
            
        except mysql.connector.Error as err:
            QMessageBox.critical(self, "Error", f"Failed to load tables:\n{err}")
    
    def select_all_tables(self):
        self.tables_list.selectAll()
        self.update_selected_count()
    
    def select_no_tables(self):
        self.tables_list.clearSelection()
        self.update_selected_count()
    
    def update_selected_count(self):
        selected_items = self.tables_list.selectedItems()
        count = len(selected_items)
        total = self.tables_list.count()
        
        self.selected_count_label.setText(f"Selected: {count} of {total} tables")
        

        self.start_export_btn.setEnabled(count > 0)
    
    def browse_output_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Output Directory", 
            self.output_dir_input.text()
        )
        if directory:
            self.output_dir_input.setText(directory)
    
    def start_export(self):

        selected_items = self.tables_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select at least one table to export")
            return
        
        selected_tables = [item.text() for item in selected_items]
        

        export_format = "single" if self.single_file_radio.isChecked() else "separate"
        

        output_dir = self.output_dir_input.text()
        if not output_dir or not os.path.exists(output_dir):
            QMessageBox.warning(self, "Warning", "Please select a valid output directory")
            return
        

        connection_params = {
            'host': self.host_input.text() or 'localhost',
            'user': self.user_input.text() or 'root',
            'password': self.password_input.text(),
            'database': self.database_input.text()
        }
        

        self.tab_widget.setCurrentIndex(3)
        

        self.overall_progress.setValue(0)
        self.overall_progress_label.setText("Starting export...")
        self.table_progress_label.setText("Preparing...")
        self.log_text.clear()
        

        self.start_export_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        

        self.export_thread = DatabaseExportThread(connection_params, selected_tables, export_format, output_dir)
        self.export_thread.progress_signal.connect(self.update_progress)
        self.export_thread.table_progress_signal.connect(self.update_table_progress)
        self.export_thread.finished_signal.connect(self.export_finished)
        self.export_thread.log_signal.connect(self.add_log_message)
        self.export_thread.start()
    
    def cancel_export(self):
        if self.export_thread and self.export_thread.isRunning():
            self.export_thread.cancel_export()
            self.add_log_message("Cancelling export...")
    
    def update_progress(self, percentage, message):
        self.overall_progress.setValue(percentage)
        self.overall_progress_label.setText(message)
    
    def update_table_progress(self, table_name, current, total):
        self.table_progress_label.setText(f"Processing: {table_name} ({current}/{total})")
    
    def add_log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        self.log_text.clear()
    
    def export_finished(self, success, message):
        self.overall_progress.setValue(100 if success else 0)
        self.overall_progress_label.setText("Export completed" if success else "Export failed")
        self.table_progress_label.setText("Finished" if success else "Cancelled/Failed")
        

        self.start_export_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        

        if success:
            QMessageBox.information(self, "Export Complete", message)
            self.statusBar().showMessage("Export completed successfully")
        else:
            QMessageBox.warning(self, "Export Failed", message)
            self.statusBar().showMessage("Export failed or cancelled")
        
        self.add_log_message("Export finished")

def main():
    app = QApplication(sys.argv)
    

    app.setStyle('Fusion')
    

    window = MySQLtoJSONGUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
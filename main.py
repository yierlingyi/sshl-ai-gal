import sys
import asyncio
import qasync
import traceback
from PySide6.QtWidgets import QApplication, QMessageBox
from src.frontend.main_window import MainWindow

def main():
    try:
        # Setup Application
        app = QApplication(sys.argv)
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        
        # Create and Show Window
        print("Initializing MainWindow...")
        window = MainWindow()
        window.show()
        print("MainWindow shown. Starting Event Loop.")
        
        # Run Loop
        with loop:
           loop.run_forever()
        # sys.exit(app.exec())
            
    except Exception as e:
        print("CRITICAL ERROR:")
        traceback.print_exc()
        # Try to show message box if app is initialized
        if 'app' in locals():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText(f"Error: {str(e)}")
            msg.setDetailedText(traceback.format_exc())
            msg.exec()

if __name__ == "__main__":
    main()


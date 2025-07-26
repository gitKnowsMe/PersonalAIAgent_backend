#!/usr/bin/env python3
"""
Enhanced Startup Script for Personal AI Agent
Handles first-run experience with guided model download and setup.
"""

import os
import sys
import time
import webbrowser
import subprocess
import logging
import threading
from pathlib import Path
import json
from datetime import datetime

# Setup logging
log_dir = Path.home() / "Library" / "Logs" / "PersonalAIAgent"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "startup.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class FirstRunExperience:
    def __init__(self):
        self.app_support_dir = Path.home() / "Library" / "Application Support" / "PersonalAIAgent"
        self.data_dir = self.app_support_dir / "data" 
        self.models_dir = self.app_support_dir / "models"
        self.config_file = self.app_support_dir / "config.json"
        self.first_run_marker = self.app_support_dir / ".first_run_completed"
        
    def is_first_run(self):
        """Check if this is the first run."""
        return not self.first_run_marker.exists()
    
    def create_directory_structure(self):
        """Create necessary directory structure."""
        logger.info("Creating application directory structure...")
        
        directories = [
            self.app_support_dir,
            self.data_dir,
            self.data_dir / "uploads",
            self.data_dir / "vector_db",
            self.data_dir / "vector_db" / "financial",
            self.data_dir / "vector_db" / "long_form", 
            self.data_dir / "vector_db" / "generic",
            self.data_dir / "vector_db" / "emails",
            self.data_dir / "emails",
            self.models_dir,
            log_dir,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
    
    def create_configuration(self):
        """Create initial configuration."""
        logger.info("Creating initial configuration...")
        
        # Set environment variables for portable mode
        os.environ['PORTABLE_MODE'] = 'true'
        os.environ['DATABASE_URL'] = f'sqlite:///{self.data_dir}/personal_ai_agent_portable.db'
        os.environ['HOST'] = 'localhost'
        os.environ['PORT'] = '8000'
        os.environ['DEBUG'] = 'false'
        os.environ['LLM_MODEL_PATH'] = str(self.models_dir / 'phi-2-instruct-Q4_K_M.gguf')
        os.environ['USE_METAL'] = 'true'
        os.environ['METAL_N_GPU_LAYERS'] = '1'
        
        # Create config file
        config = {
            "version": "1.0.0",
            "first_run_completed": False,
            "installation_date": datetime.now().isoformat(),
            "data_directory": str(self.data_dir),
            "models_directory": str(self.models_dir),
            "database_url": f'sqlite:///{self.data_dir}/personal_ai_agent_portable.db',
            "server": {
                "host": "localhost",
                "port": 8000
            },
            "models": {
                "llm_model": "phi-2-instruct-Q4_K_M.gguf",
                "embedding_model": "all-MiniLM-L6-v2",
                "download_completed": False
            },
            "features": {
                "gmail_integration": False,
                "pdf_processing": True,
                "local_ai": True
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Configuration created: {self.config_file}")
    
    def models_exist(self):
        """Check if required models exist."""
        llm_model = self.models_dir / 'phi-2-instruct-Q4_K_M.gguf'
        embedding_model_dir = self.models_dir / 'all-MiniLM-L6-v2'
        
        return llm_model.exists() and embedding_model_dir.exists()
    
    def show_welcome_dialog(self):
        """Show welcome dialog using native macOS notification."""
        logger.info("Showing welcome message...")
        
        try:
            # Use osascript to show native dialog
            script = '''
            display dialog "Welcome to Personal AI Agent!

This is your first launch. The app will now:
• Download the Phi-2 AI model (~1.7GB)
• Set up your private database
• Initialize the web interface

This may take a few minutes. Once complete, your browser will open automatically." \\
            with title "Personal AI Agent - First Run Setup" \\
            buttons {"OK"} \\
            default button "OK" \\
            with icon note
            '''
            
            subprocess.run(['osascript', '-e', script], check=False)
        except Exception as e:
            logger.warning(f"Could not show welcome dialog: {e}")
            print("\n" + "="*60)
            print("🚀 WELCOME TO PERSONAL AI AGENT!")
            print("="*60)
            print("This is your first launch. Setting up your private AI assistant...")
            print("• Downloading Phi-2 AI model (~1.7GB)")
            print("• Creating your private database")
            print("• Initializing the web interface")
            print("\nThis may take a few minutes. Please wait...")
            print("="*60 + "\n")
    
    def download_models_with_progress(self):
        """Download models with progress reporting."""
        logger.info("Starting model download...")
        
        try:
            # Import and run the model download
            sys.path.insert(0, str(Path(__file__).parent))
            
            # Try to import the download script
            try:
                import download_model
                import download_embedding_model
                
                logger.info("Downloading Phi-2 model...")
                download_model.main()
                
                logger.info("Downloading embedding model...")
                download_embedding_model.main()
                
            except ImportError as e:
                logger.warning(f"Could not import download modules: {e}")
                # Fallback: call as subprocess
                python_exe = sys.executable
                base_dir = Path(__file__).parent
                
                logger.info("Downloading models via subprocess...")
                
                # Download LLM model
                result = subprocess.run([
                    python_exe, str(base_dir / 'download_model.py')
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"LLM model download failed: {result.stderr}")
                    return False
                
                # Download embedding model
                result = subprocess.run([
                    python_exe, str(base_dir / 'download_embedding_model.py')
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"Embedding model download failed: {result.stderr}")
                    return False
            
            # Update config
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                config['models']['download_completed'] = True
                with open(self.config_file, 'w') as f:
                    json.dump(config, f, indent=2)
            
            logger.info("Model download completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Model download failed: {e}")
            return False
    
    def setup_database(self):
        """Set up the SQLite database."""
        logger.info("Setting up database...")
        
        try:
            # Import and initialize database
            sys.path.insert(0, str(Path(__file__).parent))
            
            # Set environment for portable mode
            os.environ['PORTABLE_MODE'] = 'true'
            os.environ['DATABASE_URL'] = f'sqlite:///{self.data_dir}/personal_ai_agent_portable.db'
            
            # Try to import and run database setup
            try:
                import setup_db
                setup_db.main()
                
                # Create admin user
                import create_admin
                create_admin.main()
                
            except ImportError:
                # Fallback: run as subprocess
                python_exe = sys.executable
                base_dir = Path(__file__).parent
                
                subprocess.run([python_exe, str(base_dir / 'setup_db.py')], check=True)
                subprocess.run([python_exe, str(base_dir / 'create_admin.py')], check=True)
            
            logger.info("Database setup completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            return False
    
    def create_desktop_alias(self):
        """Create desktop alias for easy access."""
        try:
            desktop = Path.home() / "Desktop"
            app_path = Path(__file__).parent.parent  # Assuming we're in Contents/MacOS
            
            if app_path.name.endswith('.app'):
                alias_script = f'''
                tell application "Finder"
                    make alias file to POSIX file "{app_path}" at desktop
                    set name of result to "Personal AI Agent"
                end tell
                '''
                
                subprocess.run(['osascript', '-e', alias_script], check=False)
                logger.info("Created desktop alias")
                
        except Exception as e:
            logger.warning(f"Could not create desktop alias: {e}")
    
    def auto_open_browser(self):
        """Auto-open browser after successful setup."""
        logger.info("Opening browser...")
        
        def delayed_open():
            time.sleep(3)  # Wait for server to start
            try:
                webbrowser.open('http://localhost:8000')
                logger.info("Browser opened successfully")
            except Exception as e:
                logger.warning(f"Could not open browser: {e}")
        
        # Open browser in background thread
        thread = threading.Thread(target=delayed_open, daemon=True)
        thread.start()
    
    def mark_first_run_complete(self):
        """Mark first run as completed."""
        self.first_run_marker.touch()
        
        # Update config
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            config['first_run_completed'] = True
            config['setup_completed_date'] = datetime.now().isoformat()
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        
        logger.info("First run setup completed!")
    
    def run_first_run_setup(self):
        """Run the complete first-run setup process."""
        logger.info("🚀 Starting Personal AI Agent first-run setup...")
        
        try:
            # Step 1: Create directories
            self.create_directory_structure()
            
            # Step 2: Create configuration
            self.create_configuration()
            
            # Step 3: Show welcome
            self.show_welcome_dialog()
            
            # Step 4: Check and download models
            if not self.models_exist():
                logger.info("Models not found, downloading...")
                if not self.download_models_with_progress():
                    logger.error("Model download failed, continuing with setup...")
            else:
                logger.info("Models already exist, skipping download")
            
            # Step 5: Setup database
            if not self.setup_database():
                logger.error("Database setup failed, continuing...")
            
            # Step 6: Create desktop alias (optional)
            self.create_desktop_alias()
            
            # Step 7: Mark as complete
            self.mark_first_run_complete()
            
            # Step 8: Auto-open browser
            self.auto_open_browser()
            
            logger.info("🎉 First-run setup completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"First-run setup failed: {e}")
            return False

def main():
    """Main entry point."""
    logger.info("Personal AI Agent starting...")
    
    # Handle first-run experience
    first_run = FirstRunExperience()
    
    if first_run.is_first_run():
        logger.info("First run detected, starting setup...")
        if not first_run.run_first_run_setup():
            logger.error("First-run setup failed, starting app anyway...")
    else:
        logger.info("Returning user, skipping first-run setup")
        
        # Still auto-open browser for returning users
        first_run.auto_open_browser()
    
    # Import and start the main application
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Set portable mode environment
        os.environ['PORTABLE_MODE'] = 'true'
        data_dir = Path.home() / "Library" / "Application Support" / "PersonalAIAgent" / "data"
        os.environ['DATABASE_URL'] = f'sqlite:///{data_dir}/personal_ai_agent_portable.db'
        
        # Import and run the main app
        from app.main import app
        import uvicorn
        
        logger.info("Starting FastAPI server...")
        uvicorn.run(
            app,
            host='localhost',
            port=8000,
            log_level='info',
            access_log=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
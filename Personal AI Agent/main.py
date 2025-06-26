import uvicorn
import os
import logging
from app.core.config import settings

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join("logs", "app.log")),
            logging.StreamHandler()
        ]
    )
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Run the server
    uvicorn.run(
        "app.main:app",
        host="localhost",
        port=8000,
        reload=True
    ) 
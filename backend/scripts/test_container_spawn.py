import sys
import os
import logging

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.container_service import ContainerService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_container_lifecycle():
    logger.info("🧪 Starting Container Lifecycle Test...")
    
    service = ContainerService()
    if not service.client:
        logger.error("❌ Docker client not available. Test skipped.")
        return

    # 1. Spawn
    logger.info("1️⃣ Spawning container...")
    container = service.create_container(
        image="node:20-alpine", 
        name="innexar-test-container",
        command="tail -f /dev/null" # Keep alive
    )
    
    if not container:
        logger.error("❌ Failed to spawn container.")
        return

    try:
        # 1.5 Setup Workspace
        logger.info("1️⃣.5️⃣ Creating /app directory...")
        service.execute_command(container.id, "mkdir -p /app")

        # 2. Execute Command
        logger.info("2️⃣ Executing command: 'echo Hello Innexar'...")
        result = service.execute_command(container.id, "echo 'Hello Innexar'")
        logger.info(f"   Output: {result['output'].strip()}")
        
        if "Hello Innexar" in result['output']:
            logger.info("✅ Command execution verified.")
        else:
            logger.error("❌ Command execution failed.")

        # 3. Write/Read File
        logger.info("3️⃣ Testing File I/O...")
        service.write_file(container.id, "/app/test.txt", "File Content Works")
        read_content = service.read_file(container.id, "/app/test.txt")
        logger.info(f"   Read content: {read_content}")

        if "File Content Works" in (read_content or ""):
            logger.info("✅ File I/O verified.")
        else:
            logger.error("❌ File I/O failed.")

    finally:
        # 4. Cleanup
        logger.info("4️⃣ destroying container...")
        service.destroy_container(container.id)
        logger.info("✅ Cleanup done.")

if __name__ == "__main__":
    test_container_lifecycle()

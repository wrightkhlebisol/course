"""
Demonstration script for Flink stream processing
"""

import time
import yaml
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sources.log_generator import LogGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_demo():
    """Run complete demonstration"""
    logger.info("🎬 Starting Flink Stream Processing Demonstration")
    
    # Load config
    with open("config/flink_config.yaml", 'r') as f:
        config = yaml.safe_load(f)
        
    generator = LogGenerator(config['sources']['rabbitmq'])
    
    try:
        generator.connect()
        
        logger.info("\n📊 Phase 1: Generating normal traffic (30 seconds)")
        generator.generate_normal_traffic(duration_seconds=30, rate=20)
        
        time.sleep(5)
        
        logger.info("\n💉 Phase 2: Injecting authentication spike")
        generator.inject_auth_spike('attack_user', count=15)
        
        time.sleep(5)
        
        logger.info("\n💉 Phase 3: Injecting latency degradation")
        generator.inject_latency_spike(duration_seconds=30)
        
        time.sleep(5)
        
        logger.info("\n💉 Phase 4: Injecting cascading failure")
        generator.inject_cascading_failure()
        
        time.sleep(5)
        
        logger.info("\n📊 Phase 5: Resuming normal traffic (30 seconds)")
        generator.generate_normal_traffic(duration_seconds=30, rate=20)
        
        logger.info("\n✅ Demonstration complete!")
        logger.info("🌐 Check dashboard at: http://localhost:8080")
        
    finally:
        generator.close()


if __name__ == "__main__":
    run_demo()

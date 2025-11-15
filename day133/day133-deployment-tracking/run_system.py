#!/usr/bin/env python3
"""
Main execution script for Deployment Tracking System
"""

import os
import sys
import subprocess
import time

def run_command(command, check=True):
    """Run a shell command"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    
    if result.stdout:
        print(result.stdout)
    
    return True

def main():
    print("🚀 Deployment Tracking System - Full Setup")
    print("=" * 50)
    
    # Check Python version
    print("1. Checking Python version...")
    if not run_command("python3 --version"):
        print("Error: Python 3.11 not found")
        return False
    
    # Create virtual environment and install dependencies
    print("\n2. Setting up Python environment...")
    if not run_command("chmod +x build.sh && ./build.sh"):
        print("Error: Build failed")
        return False
    
    # Start services
    print("\n3. Starting services...")
    if not run_command("chmod +x start.sh && ./start.sh"):
        print("Error: Failed to start services")
        return False
    
    # Wait for services to be ready
    print("\n4. Waiting for services to be ready...")
    time.sleep(20)
    
    # Run demo
    print("\n5. Running system demonstration...")
    if not run_command("python demo.py"):
        print("Warning: Demo had issues, but system may still be functional")
    
    print("\n🎉 System is ready!")
    print("📊 Dashboard: http://localhost:8000")
    print("🔍 API: http://localhost:8000/api/deployments")
    print("\nTo stop the system, run: ./stop.sh")

if __name__ == "__main__":
    main()

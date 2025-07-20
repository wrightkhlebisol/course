#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎯 Compliance Reports System - Help Guide${NC}"
echo -e "${BLUE}=========================================${NC}"

echo -e "\n${PURPLE}📋 Available Scripts${NC}"
echo -e "${PURPLE}===================${NC}"

echo -e "\n${CYAN}🚀 start.sh${NC}"
echo -e "   Starts the compliance reports system"
echo -e "   ${YELLOW}Usage:${NC}"
echo -e "     ./start.sh              # Start with Docker (recommended)"
echo -e "     ./start.sh --no-docker  # Start manually (development)"
echo -e "     ./start.sh --demo       # Start and run demo automatically"
echo -e "   ${YELLOW}Features:${NC}"
echo -e "     • Automatic port checking"
echo -e "     • Health monitoring"
echo -e "     • Docker and manual modes"
echo -e "     • Dependency installation"

echo -e "\n${CYAN}🛑 stop.sh${NC}"
echo -e "   Stops the compliance reports system"
echo -e "   ${YELLOW}Usage:${NC}"
echo -e "     ./stop.sh               # Stop the system"
echo -e "     ./stop.sh --clean       # Stop and clean up resources"
echo -e "   ${YELLOW}Features:${NC}"
echo -e "     • Graceful shutdown"
echo -e "     • Process cleanup"
echo -e "     • Port verification"
echo -e "     • Resource cleanup"

echo -e "\n${CYAN}🎬 demo.sh${NC}"
echo -e "   Runs an interactive demonstration"
echo -e "   ${YELLOW}Usage:${NC}"
echo -e "     ./demo.sh               # Run interactive demo"
echo -e "   ${YELLOW}Features:${NC}"
echo -e "     • Step-by-step walkthrough"
echo -e "     • Browser integration"
echo -e "     • API testing"
echo -e "     • Report generation"

echo -e "\n${CYAN}📊 status.sh${NC}"
echo -e "   Checks system status and health"
echo -e "   ${YELLOW}Usage:${NC}"
echo -e "     ./status.sh             # Check system status"
echo -e "   ${YELLOW}Features:${NC}"
echo -e "     • Service health checks"
echo -e "     • Port monitoring"
echo -e "     • Log file inspection"
echo -e "     • Docker container status"

echo -e "\n${CYAN}❓ help.sh${NC}"
echo -e "   Shows this help information"
echo -e "   ${YELLOW}Usage:${NC}"
echo -e "     ./help.sh               # Show help (this script)"

echo -e "\n${PURPLE}🚀 Quick Start Examples${NC}"
echo -e "${PURPLE}=======================${NC}"

echo -e "\n${GREEN}1. Quick Demo (Recommended)${NC}"
echo -e "   ./start.sh --demo"
echo -e "   # This will start the system and run the demo automatically"

echo -e "\n${GREEN}2. Development Mode${NC}"
echo -e "   ./start.sh --no-docker"
echo -e "   # Start manually for development and debugging"

echo -e "\n${GREEN}3. Production Deployment${NC}"
echo -e "   ./start.sh"
echo -e "   # Start with Docker for production use"

echo -e "\n${GREEN}4. Interactive Demo${NC}"
echo -e "   ./start.sh"
echo -e "   ./demo.sh"
echo -e "   # Start system first, then run interactive demo"

echo -e "\n${GREEN}5. System Monitoring${NC}"
echo -e "   ./status.sh"
echo -e "   # Check if everything is running properly"

echo -e "\n${PURPLE}🎯 Demo Features Showcased${NC}"
echo -e "${PURPLE}=========================${NC}"

echo -e "\n${CYAN}📊 Dashboard Overview${NC}"
echo -e "   • Real-time system statistics"
echo -e "   • Recent compliance reports"
echo -e "   • Framework-specific metrics"
echo -e "   • Quick action buttons"

echo -e "\n${CYAN}📋 Report Generation${NC}"
echo -e "   • SOX Compliance (Financial controls)"
echo -e "   • HIPAA Compliance (Healthcare privacy)"
echo -e "   • PCI-DSS Compliance (Payment security)"
echo -e "   • GDPR Compliance (Data protection)"

echo -e "\n${CYAN}📄 Export Capabilities${NC}"
echo -e "   • PDF reports with professional formatting"
echo -e "   • CSV data exports for analysis"
echo -e "   • JSON structured data"
echo -e "   • XML compliance documents"

echo -e "\n${CYAN}🔐 Advanced Features${NC}"
echo -e "   • Cryptographic signature verification"
echo -e "   • Background report processing"
echo -e "   • Scheduled report automation"
echo -e "   • Real-time status monitoring"

echo -e "\n${PURPLE}🌐 System URLs${NC}"
echo -e "${PURPLE}===============${NC}"
echo -e "${CYAN}Dashboard:${NC} http://localhost:3000"
echo -e "${CYAN}API Docs:${NC} http://localhost:8000/docs"
echo -e "${CYAN}API Base:${NC} http://localhost:8000"

echo -e "\n${PURPLE}📚 Learning Outcomes${NC}"
echo -e "${PURPLE}===================${NC}"
echo -e "This project demonstrates:"
echo -e "  • Multi-framework compliance engine"
echo -e "  • Automated report generation"
echo -e "  • Cryptographic integrity verification"
echo -e "  • Modern web dashboard (React + Material-UI)"
echo -e "  • RESTful API design (FastAPI)"
echo -e "  • Container orchestration (Docker Compose)"
echo -e "  • Scheduled automation"
echo -e "  • Export flexibility"

echo -e "\n${PURPLE}🛠️  Troubleshooting${NC}"
echo -e "${PURPLE}===================${NC}"
echo -e "${YELLOW}Port conflicts:${NC} Use ./stop.sh to stop existing services"
echo -e "${YELLOW}Docker issues:${NC} Use ./stop.sh --clean to clean up"
echo -e "${YELLOW}Permission errors:${NC} Run chmod +x *.sh"
echo -e "${YELLOW}Service not starting:${NC} Check logs in logs/ directory"

echo -e "\n${GREEN}🎉 Ready to get started?${NC}"
echo -e "Run: ${CYAN}./start.sh --demo${NC} for the quickest experience!" 
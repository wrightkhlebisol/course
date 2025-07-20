#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"

echo -e "${BLUE}🎬 Compliance Reports System Demo${NC}"
echo -e "${BLUE}===============================${NC}"

# Function to check if service is running
check_service() {
    local url=$1
    local service_name=$2
    
    if curl -s "$url" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to wait for user input
wait_for_user() {
    echo -e "\n${YELLOW}Press Enter to continue...${NC}"
    read -r
}

# Function to open URL in browser
open_browser() {
    local url=$1
    local description=$2
    
    echo -e "${CYAN}🌐 Opening $description...${NC}"
    
    if command -v open &> /dev/null; then
        open "$url"
    elif command -v xdg-open &> /dev/null; then
        xdg-open "$url"
    else
        echo -e "${YELLOW}Please manually open: $url${NC}"
    fi
}

# Check if services are running
echo -e "${YELLOW}🔍 Checking if services are running...${NC}"

if ! check_service "$BACKEND_URL/" "Backend API"; then
    echo -e "${RED}❌ Backend API is not running${NC}"
    echo -e "${YELLOW}💡 Please start the system first with: ./start.sh${NC}"
    exit 1
fi

if ! check_service "$FRONTEND_URL" "Frontend"; then
    echo -e "${RED}❌ Frontend is not running${NC}"
    echo -e "${YELLOW}💡 Please start the system first with: ./start.sh${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All services are running!${NC}"

# Demo introduction
echo -e "\n${PURPLE}🎯 Demo Overview${NC}"
echo -e "${PURPLE}===============${NC}"
echo -e "This demo will showcase:"
echo -e "  📊 Dashboard overview and statistics"
echo -e "  📋 Report generation for different compliance frameworks"
echo -e "  📅 Scheduled report management"
echo -e "  📄 Report export and download capabilities"
echo -e "  🔐 Cryptographic signature verification"
echo -e "  📈 Real-time monitoring and alerts"

wait_for_user

# Step 1: Open Dashboard
echo -e "\n${BLUE}📊 Step 1: Dashboard Overview${NC}"
echo -e "${BLUE}===========================${NC}"
echo -e "Opening the main dashboard to show:"
echo -e "  • System overview and statistics"
echo -e "  • Recent compliance reports"
echo -e "  • Framework-specific metrics"
echo -e "  • Quick action buttons"

open_browser "$FRONTEND_URL" "Compliance Dashboard"

wait_for_user

# Step 2: API Documentation
echo -e "\n${BLUE}📚 Step 2: API Documentation${NC}"
echo -e "${BLUE}===========================${NC}"
echo -e "Opening API documentation to show:"
echo -e "  • Available endpoints"
echo -e "  • Request/response schemas"
echo -e "  • Interactive API testing"
echo -e "  • Authentication methods"

open_browser "$BACKEND_URL/docs" "API Documentation"

wait_for_user

# Step 3: Run Python Demo
echo -e "\n${BLUE}🐍 Step 3: Automated Demo Script${NC}"
echo -e "${BLUE}===============================${NC}"
echo -e "Running automated demo to generate:"
echo -e "  • Sample SOX compliance reports"
echo -e "  • HIPAA audit reports"
echo -e "  • PDF and CSV exports"
echo -e "  • Cryptographic signatures"

if [ -f "scripts/demo.py" ]; then
    echo -e "${YELLOW}🎬 Running automated demo...${NC}"
    python scripts/demo.py
else
    echo -e "${RED}❌ Demo script not found${NC}"
fi

wait_for_user

# Step 4: Interactive Report Generation
echo -e "\n${BLUE}📋 Step 4: Interactive Report Generation${NC}"
echo -e "${BLUE}=========================================${NC}"
echo -e "Now let's generate some reports interactively:"

# Generate SOX Report
echo -e "\n${CYAN}📊 Generating SOX Compliance Report...${NC}"
curl -X POST "$BACKEND_URL/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "framework": "SOX",
    "period_start": "2024-01-01T00:00:00",
    "period_end": "2024-01-31T23:59:59",
    "export_format": "pdf",
    "title": "January 2024 SOX Compliance Report",
    "description": "Monthly SOX compliance report for financial controls"
  }' | jq '.'

wait_for_user

# Generate HIPAA Report
echo -e "\n${CYAN}🏥 Generating HIPAA Compliance Report...${NC}"
curl -X POST "$BACKEND_URL/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "framework": "HIPAA",
    "period_start": "2024-01-01T00:00:00",
    "period_end": "2024-01-31T23:59:59",
    "export_format": "csv",
    "title": "January 2024 HIPAA Audit Report",
    "description": "Monthly HIPAA compliance audit for patient data protection"
  }' | jq '.'

wait_for_user

# Step 5: Check Report Status
echo -e "\n${BLUE}📈 Step 5: Report Status Monitoring${NC}"
echo -e "${BLUE}=====================================${NC}"
echo -e "Checking the status of generated reports:"

# List all reports
echo -e "\n${CYAN}📋 Listing all reports...${NC}"
curl -s "$BACKEND_URL/reports" | jq '.'

wait_for_user

# Step 6: Dashboard Statistics
echo -e "\n${BLUE}📊 Step 6: Dashboard Statistics${NC}"
echo -e "${BLUE}=================================${NC}"
echo -e "Fetching real-time dashboard statistics:"

echo -e "\n${CYAN}📈 Getting dashboard stats...${NC}"
curl -s "$BACKEND_URL/dashboard/stats" | jq '.'

wait_for_user

# Step 7: Compliance Frameworks
echo -e "\n${BLUE}🏛️  Step 7: Compliance Frameworks${NC}"
echo -e "${BLUE}=================================${NC}"
echo -e "Exploring supported compliance frameworks:"

echo -e "\n${CYAN}📚 Available frameworks...${NC}"
curl -s "$BACKEND_URL/frameworks" | jq '.'

wait_for_user

# Step 8: Scheduled Reports
echo -e "\n${BLUE}📅 Step 8: Scheduled Reports Management${NC}"
echo -e "${BLUE}=========================================${NC}"
echo -e "Setting up automated report scheduling:"

# Create a scheduled report
echo -e "\n${CYAN}📅 Creating scheduled SOX report...${NC}"
curl -X POST "$BACKEND_URL/reports/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "framework": "SOX",
    "export_format": "pdf",
    "schedule_type": "weekly",
    "recipients": ["compliance@company.com", "audit@company.com"],
    "enabled": true
  }' | jq '.'

wait_for_user

# List scheduled reports
echo -e "\n${CYAN}📋 Listing scheduled reports...${NC}"
curl -s "$BACKEND_URL/reports/schedule" | jq '.'

wait_for_user

# Step 9: Return to Dashboard
echo -e "\n${BLUE}🏠 Step 9: Return to Dashboard${NC}"
echo -e "${BLUE}=================================${NC}"
echo -e "Opening the dashboard again to see:"
echo -e "  • Newly generated reports"
echo -e "  • Updated statistics"
echo -e "  • Scheduled reports"
echo -e "  • Download options"

open_browser "$FRONTEND_URL" "Updated Dashboard"

wait_for_user

# Demo summary
echo -e "\n${PURPLE}🎉 Demo Summary${NC}"
echo -e "${PURPLE}==============${NC}"
echo -e "${GREEN}✅ Dashboard overview demonstrated${NC}"
echo -e "${GREEN}✅ API documentation explored${NC}"
echo -e "${GREEN}✅ Automated report generation tested${NC}"
echo -e "${GREEN}✅ Interactive report creation shown${NC}"
echo -e "${GREEN}✅ Report status monitoring demonstrated${NC}"
echo -e "${GREEN}✅ Dashboard statistics displayed${NC}"
echo -e "${GREEN}✅ Compliance frameworks overview${NC}"
echo -e "${GREEN}✅ Scheduled reports management${NC}"

echo -e "\n${CYAN}🚀 Key Features Demonstrated:${NC}"
echo -e "  • Multi-framework compliance support (SOX, HIPAA, PCI-DSS, GDPR)"
echo -e "  • Automated report generation with background processing"
echo -e "  • Multiple export formats (PDF, CSV, JSON, XML)"
echo -e "  • Cryptographic signature verification"
echo -e "  • Real-time dashboard with statistics"
echo -e "  • Scheduled report automation"
echo -e "  • RESTful API with comprehensive documentation"
echo -e "  • Modern React frontend with Material-UI"

echo -e "\n${YELLOW}💡 Next Steps:${NC}"
echo -e "  • Explore the dashboard interface"
echo -e "  • Generate custom reports"
echo -e "  • Set up automated scheduling"
echo -e "  • Configure compliance frameworks"
echo -e "  • Review API documentation"
echo -e "  • Test different export formats"

echo -e "\n${GREEN}🎊 Demo completed successfully!${NC}"
echo -e "${YELLOW}🌐 Dashboard: $FRONTEND_URL${NC}"
echo -e "${YELLOW}📚 API Docs: $BACKEND_URL/docs${NC}" 
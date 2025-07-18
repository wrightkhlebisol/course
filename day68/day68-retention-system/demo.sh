#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Demo script for Day 68: Data Retention System
echo -e "${BLUE}"
echo "🎯 Day 68: Data Retention System - Interactive Demo"
echo "=================================================="
echo -e "${NC}"

# Check if system is running
check_system_status() {
    echo -e "${CYAN}🔍 Checking system status...${NC}"
    
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend API is running${NC}"
    else
        echo -e "${RED}❌ Backend API is not running${NC}"
        echo -e "${YELLOW}Please start the system with: ./start.sh${NC}"
        exit 1
    fi
    
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend is running${NC}"
    else
        echo -e "${RED}❌ Frontend is not running${NC}"
        echo -e "${YELLOW}Please start the system with: ./start.sh${NC}"
        exit 1
    fi
    
    echo ""
}

# Show initial metrics
show_initial_metrics() {
    echo -e "${CYAN}📊 Initial System Metrics${NC}"
    echo "================================"
    
    metrics=$(curl -s http://localhost:8000/api/retention/metrics)
    
    echo -e "${GREEN}Total Policies:${NC} $(echo $metrics | jq -r '.total_policies')"
    echo -e "${GREEN}Active Jobs:${NC} $(echo $metrics | jq -r '.active_jobs')"
    echo -e "${GREEN}Storage Freed:${NC} $(echo $metrics | jq -r '.storage_freed_gb') GB"
    echo -e "${GREEN}Compliance Score:${NC} $(echo $metrics | jq -r '.compliance_score')%"
    echo -e "${GREEN}Logs Processed Today:${NC} $(echo $metrics | jq -r '.logs_processed_today')"
    echo -e "${GREEN}Logs Deleted Today:${NC} $(echo $metrics | jq -r '.logs_deleted_today')"
    echo -e "${GREEN}Logs Archived Today:${NC} $(echo $metrics | jq -r '.logs_archived_today')"
    echo ""
}

# Demo log generation
demo_log_generation() {
    echo -e "${CYAN}📝 Demo: Log Generation${NC}"
    echo "=========================="
    
    echo -e "${YELLOW}Generating sample logs...${NC}"
    response=$(curl -s -X POST "http://localhost:8000/api/logs/generate?count=50")
    count=$(echo $response | jq -r '.count')
    echo -e "${GREEN}✅ Generated $count sample log files${NC}"
    
    echo -e "${YELLOW}Getting log statistics...${NC}"
    stats=$(curl -s http://localhost:8000/api/logs/stats)
    total_files=$(echo $stats | jq -r '.stats.total_files')
    total_size=$(echo $stats | jq -r '.stats.total_size_mb')
    
    echo -e "${GREEN}📁 Total Log Files: $total_files${NC}"
    echo -e "${GREEN}💾 Total Size: ${total_size} MB${NC}"
    
    # Show storage breakdown
    echo -e "${BLUE}Storage Breakdown:${NC}"
    hot_files=$(echo $stats | jq -r '.stats.by_storage.hot.files')
    warm_files=$(echo $stats | jq -r '.stats.by_storage.warm.files')
    cold_files=$(echo $stats | jq -r '.stats.by_storage.cold.files')
    
    echo -e "  🔥 Hot Storage: $hot_files files"
    echo -e "  🌡️  Warm Storage: $warm_files files"
    echo -e "  ❄️  Cold Storage: $cold_files files"
    echo ""
}

# Demo log search
demo_log_search() {
    echo -e "${CYAN}🔍 Demo: Log Search & Filtering${NC}"
    echo "=================================="
    
    echo -e "${YELLOW}Searching for security logs in hot storage...${NC}"
    security_logs=$(curl -s "http://localhost:8000/api/logs/search?storage_type=hot&log_type=security&limit=3")
    count=$(echo $security_logs | jq -r '.count')
    echo -e "${GREEN}✅ Found $count security logs in hot storage${NC}"
    
    echo -e "${YELLOW}Sample security log:${NC}"
    first_log=$(echo $security_logs | jq -r '.logs[0]')
    timestamp=$(echo $first_log | jq -r '.timestamp')
    message=$(echo $first_log | jq -r '.message')
    level=$(echo $first_log | jq -r '.level')
    
    echo -e "  📅 Timestamp: $timestamp"
    echo -e "  🛡️  Message: $message"
    echo -e "  ⚠️  Level: $level"
    echo ""
}

# Demo simulation
demo_simulation() {
    echo -e "${CYAN}🎮 Demo: Retention Simulation${NC}"
    echo "================================="
    
    echo -e "${YELLOW}Starting retention job simulation...${NC}"
    
    # Step 1: Start job
    echo -e "${BLUE}Step 1: Starting retention job...${NC}"
    start_response=$(curl -s -X POST http://localhost:8000/api/retention/simulate/start)
    active_jobs=$(echo $start_response | jq -r '.active_jobs')
    echo -e "${GREEN}✅ Active jobs: $active_jobs${NC}"
    
    sleep 2
    
    # Step 2: Process logs
    echo -e "${BLUE}Step 2: Processing logs...${NC}"
    process_response=$(curl -s -X POST http://localhost:8000/api/retention/simulate/process)
    logs_processed=$(echo $process_response | jq -r '.logs_processed')
    logs_deleted=$(echo $process_response | jq -r '.logs_deleted')
    logs_archived=$(echo $process_response | jq -r '.logs_archived')
    echo -e "${GREEN}✅ Processed: $logs_processed logs${NC}"
    echo -e "${GREEN}✅ Deleted: $logs_deleted logs${NC}"
    echo -e "${GREEN}✅ Archived: $logs_archived logs${NC}"
    
    sleep 2
    
    # Step 3: Update storage
    echo -e "${BLUE}Step 3: Updating storage...${NC}"
    storage_response=$(curl -s -X POST http://localhost:8000/api/retention/simulate/storage)
    storage_freed=$(echo $storage_response | jq -r '.storage_freed_mb')
    echo -e "${GREEN}✅ Freed: $storage_freed MB of storage${NC}"
    
    sleep 2
    
    # Step 4: Complete job
    echo -e "${BLUE}Step 4: Completing job...${NC}"
    complete_response=$(curl -s -X POST http://localhost:8000/api/retention/simulate/complete)
    final_jobs=$(echo $complete_response | jq -r '.active_jobs')
    compliance_score=$(echo $complete_response | jq -r '.compliance_score')
    echo -e "${GREEN}✅ Active jobs: $final_jobs${NC}"
    echo -e "${GREEN}✅ Compliance score: $compliance_score%${NC}"
    
    echo ""
}

# Show updated metrics
show_updated_metrics() {
    echo -e "${CYAN}📊 Updated System Metrics${NC}"
    echo "================================"
    
    metrics=$(curl -s http://localhost:8000/api/retention/metrics)
    
    echo -e "${GREEN}Total Policies:${NC} $(echo $metrics | jq -r '.total_policies')"
    echo -e "${GREEN}Active Jobs:${NC} $(echo $metrics | jq -r '.active_jobs')"
    echo -e "${GREEN}Storage Freed:${NC} $(echo $metrics | jq -r '.storage_freed_gb') GB"
    echo -e "${GREEN}Compliance Score:${NC} $(echo $metrics | jq -r '.compliance_score')%"
    echo -e "${GREEN}Logs Processed Today:${NC} $(echo $metrics | jq -r '.logs_processed_today')"
    echo -e "${GREEN}Logs Deleted Today:${NC} $(echo $metrics | jq -r '.logs_deleted_today')"
    echo -e "${GREEN}Logs Archived Today:${NC} $(echo $metrics | jq -r '.logs_archived_today')"
    echo ""
}

# Demo log cleanup
demo_log_cleanup() {
    echo -e "${CYAN}🧹 Demo: Log Cleanup${NC}"
    echo "========================"
    
    echo -e "${YELLOW}Cleaning up old log files (keeping last 30 days)...${NC}"
    cleanup_response=$(curl -s -X POST "http://localhost:8000/api/logs/cleanup?days_to_keep=30")
    deleted_files=$(echo $cleanup_response | jq -r '.deleted_files')
    freed_space=$(echo $cleanup_response | jq -r '.freed_space_mb')
    
    echo -e "${GREEN}✅ Deleted: $deleted_files files${NC}"
    echo -e "${GREEN}✅ Freed: $freed_space MB of space${NC}"
    echo ""
}

# Demo reset
demo_reset() {
    echo -e "${CYAN}🔄 Demo: System Reset${NC}"
    echo "========================"
    
    echo -e "${YELLOW}Resetting simulation state to initial values...${NC}"
    reset_response=$(curl -s -X POST http://localhost:8000/api/retention/simulate/reset)
    echo -e "${GREEN}✅ System reset completed${NC}"
    echo ""
}

# Show access information
show_access_info() {
    echo -e "${CYAN}🌐 Access Information${NC}"
    echo "========================"
    
    echo -e "${GREEN}📊 Dashboard:${NC} http://localhost:3000"
    echo -e "${GREEN}🔧 API Documentation:${NC} http://localhost:8000/docs"
    echo -e "${GREEN}💚 Health Check:${NC} http://localhost:8000/health"
    echo -e "${GREEN}📝 Logs Viewer:${NC} http://localhost:3000/logs"
    echo ""
}

# Interactive menu
show_menu() {
    echo -e "${PURPLE}🎯 Interactive Demo Menu${NC}"
    echo "=========================="
    echo -e "${YELLOW}1.${NC} Run Complete Demo"
    echo -e "${YELLOW}2.${NC} Show Current Metrics"
    echo -e "${YELLOW}3.${NC} Generate Logs"
    echo -e "${YELLOW}4.${NC} Search Logs"
    echo -e "${YELLOW}5.${NC} Run Simulation"
    echo -e "${YELLOW}6.${NC} Cleanup Logs"
    echo -e "${YELLOW}7.${NC} Reset System"
    echo -e "${YELLOW}8.${NC} Show Access Info"
    echo -e "${YELLOW}9.${NC} Exit"
    echo ""
}

# Run complete demo
run_complete_demo() {
    echo -e "${BLUE}🚀 Running Complete Demo...${NC}"
    echo ""
    
    check_system_status
    show_initial_metrics
    demo_log_generation
    demo_log_search
    demo_simulation
    show_updated_metrics
    demo_log_cleanup
    demo_reset
    show_access_info
    
    echo -e "${GREEN}🎉 Demo completed successfully!${NC}"
    echo ""
}

# Main demo function
main() {
    if [ "$1" = "auto" ]; then
        run_complete_demo
        return
    fi
    
    while true; do
        show_menu
        read -p "Select an option (1-9): " choice
        
        case $choice in
            1)
                run_complete_demo
                ;;
            2)
                show_initial_metrics
                ;;
            3)
                demo_log_generation
                ;;
            4)
                demo_log_search
                ;;
            5)
                demo_simulation
                ;;
            6)
                demo_log_cleanup
                ;;
            7)
                demo_reset
                ;;
            8)
                show_access_info
                ;;
            9)
                echo -e "${GREEN}👋 Thank you for using the Data Retention System Demo!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Invalid option. Please select 1-9.${NC}"
                ;;
        esac
        
        echo -e "${YELLOW}Press Enter to continue...${NC}"
        read
        clear
    done
}

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${RED}❌ Error: jq is required but not installed.${NC}"
    echo -e "${YELLOW}Please install jq: brew install jq${NC}"
    exit 1
fi

# Run main function
main "$@" 
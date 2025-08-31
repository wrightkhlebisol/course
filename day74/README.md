# Storage Format Optimization System

A comprehensive system that automatically optimizes storage formats based on query patterns, featuring an adaptive storage engine, pattern analyzer, and real-time web dashboard.

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- macOS/Linux environment
- Internet connection (for dependency installation)

### Starting the System

To build, launch, and demo the system with UI dashboard:

```bash
./start.sh
```

This script will:
1. ✅ Check Python version and dependencies
2. ✅ Install required packages if needed
3. ✅ Run all tests to ensure system integrity
4. ✅ Generate demo data with sample query patterns
5. ✅ Start the web dashboard on http://localhost:8000
6. ✅ Display real-time optimization insights

### Stopping the System

To stop all running processes and clean up:

```bash
./stop.sh
```

This script will:
1. 🛑 Gracefully stop the main application
2. 🛑 Clear any processes on port 8000
3. 🛑 Clean up all related Python processes
4. ✅ Verify all processes are stopped
5. ✅ Free up system resources

## 📊 System Features

### Adaptive Storage Engine
- **Row-oriented storage** for full record access patterns
- **Columnar storage** for analytical query patterns  
- **Hybrid storage** for mixed access patterns
- Automatic format switching based on query analysis

### Pattern Analyzer
- Real-time query pattern detection
- Performance metrics tracking
- Storage format recommendations
- Confidence scoring for optimizations

### Web Dashboard
- Real-time performance monitoring
- Storage format visualization
- Query pattern analysis
- Optimization recommendations
- Interactive charts and metrics

## 🎯 Demo Functionality

The system automatically demonstrates:

1. **Sample Data Generation**
   - Web logs with analytical query patterns
   - API logs with mixed access patterns
   - Error logs with full record access patterns

2. **Query Pattern Simulation**
   - Full record queries (row-oriented optimal)
   - Analytical queries (columnar optimal)
   - Mixed queries (hybrid optimal)

3. **Storage Optimization**
   - Automatic format recommendations
   - Performance improvement tracking
   - Real-time optimization insights

## 📁 Project Structure

```
day74/
├── start.sh                    # Start script
├── stop.sh                     # Stop script
├── setup.sh                    # Initial setup script
├── README.md                   # This file
└── storage-optimizer/          # Main project directory
    ├── src/                    # Source code
    ├── tests/                  # Test suite
    ├── demo.py                 # Demo script
    ├── requirements.txt        # Python dependencies
    └── data/                   # Storage directory
```

## 🔧 Configuration

### Port Configuration
- Dashboard runs on port 8000 by default
- Can be modified in `start.sh` and `stop.sh`

### Python Version
- Uses Python 3.11 by default
- Can be modified in `start.sh`

### Log Files
- Main application logs: `storage_optimizer.log`
- Test results: `test_results.log`
- Demo output: `demo_output.log`

## 🐛 Troubleshooting

### Port Already in Use
If port 8000 is already in use:
```bash
./stop.sh  # Stop any existing processes
./start.sh # Restart the system
```

### Python Version Issues
If you have a different Python version:
1. Edit `PYTHON_VERSION` in `start.sh`
2. Ensure the version is installed on your system

### Permission Issues
If scripts are not executable:
```bash
chmod +x start.sh stop.sh
```

### Dependencies Issues
The start script will automatically install dependencies, but if you encounter issues:
```bash
cd storage-optimizer
python3.11 -m pip install -r requirements.txt
```

## 📈 Performance Monitoring

Once the system is running, you can:

1. **Access the Dashboard**: http://localhost:8000
2. **Monitor Logs**: Check `storage_optimizer.log` for detailed logs
3. **View Test Results**: Check `test_results.log` for test output
4. **Review Demo Data**: Check `demo_output.log` for demo results

## 🎉 Success Indicators

When the system is running successfully, you should see:
- ✅ All tests passed
- ✅ Demo completed
- ✅ Dashboard started on port 8000
- ✅ Server is ready message
- ✅ Real-time optimization insights

## 🔄 Continuous Operation

The system runs continuously and will:
- Monitor query patterns in real-time
- Automatically optimize storage formats
- Update the dashboard with new insights
- Maintain performance metrics

To stop the system, simply run `./stop.sh` or press Ctrl+C in the terminal where `start.sh` is running. 
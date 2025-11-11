class DatabaseAuditDashboard {
    constructor() {
        this.socket = null;
        this.charts = {};
        this.lastLogCount = 0;
        this.init();
    }

    init() {
        this.connectWebSocket();
        this.initCharts();
        this.loadInitialData();
        
        // Refresh data every 10 seconds as fallback
        setInterval(() => this.loadInitialData(), 10000);
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.updateDashboard(data);
        };
        
        this.socket.onclose = () => {
            console.log('WebSocket connection closed, attempting to reconnect...');
            setTimeout(() => this.connectWebSocket(), 5000);
        };
        
        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    async loadInitialData() {
        try {
            const [statsResponse, logsResponse, threatsResponse] = await Promise.all([
                fetch('/api/stats'),
                fetch('/api/logs'),
                fetch('/api/threats')
            ]);
            
            const stats = await statsResponse.json();
            const logsData = await logsResponse.json();
            const threatsData = await threatsResponse.json();
            
            this.updateDashboard(stats);
            this.updateLogsTable(logsData.logs);
            this.updateThreatsTable(threatsData.threats);
            
        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }

    updateDashboard(data) {
        // Update stats
        document.getElementById('total-logs').textContent = data.total_logs || 0;
        document.getElementById('security-events').textContent = data.security_events || 0;
        document.getElementById('active-databases').textContent = Object.keys(data.databases || {}).length;
        
        // Calculate collection rate
        const currentLogCount = data.total_logs || 0;
        const rate = Math.max(0, (currentLogCount - this.lastLogCount) * 2); // per minute approximation
        document.getElementById('collection-rate').textContent = rate;
        this.lastLogCount = currentLogCount;
        
        // Update timestamp
        const lastUpdate = new Date(data.timestamp).toLocaleTimeString();
        document.getElementById('last-update').textContent = `Last update: ${lastUpdate}`;
        
        // Update charts
        this.updateDatabaseChart(data.databases);
        this.updateThreatsChart(data.threat_types);
    }

    initCharts() {
        // Database activity chart
        const dbCtx = document.getElementById('database-chart').getContext('2d');
        this.charts.database = new Chart(dbCtx, {
            type: 'doughnut',
            data: {
                labels: ['PostgreSQL', 'MySQL', 'MongoDB'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: ['#48bb78', '#ed8936', '#14b8a6'],
                    borderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#e2e8f0'
                        }
                    }
                }
            }
        });

        // Threats chart
        const threatsCtx = document.getElementById('threats-chart').getContext('2d');
        this.charts.threats = new Chart(threatsCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Threats',
                    data: [],
                    backgroundColor: '#fc8181',
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: '#e2e8f0'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1,
                            color: '#e2e8f0'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
    }

    updateDatabaseChart(databases) {
        if (!databases) return;
        
        const data = [
            databases.postgresql || 0,
            databases.mysql || 0,
            databases.mongodb || 0
        ];
        
        this.charts.database.data.datasets[0].data = data;
        this.charts.database.update();
    }

    updateThreatsChart(threatTypes) {
        if (!threatTypes) return;
        
        const labels = Object.keys(threatTypes);
        const data = Object.values(threatTypes);
        
        this.charts.threats.data.labels = labels;
        this.charts.threats.data.datasets[0].data = data;
        this.charts.threats.update();
    }

    updateLogsTable(logs) {
        const tbody = document.getElementById('logs-tbody');
        tbody.innerHTML = '';
        
        logs.slice(-20).reverse().forEach(log => {
            const row = document.createElement('tr');
            const timestamp = new Date(log.timestamp).toLocaleTimeString();
            const status = log.success ? 'Success' : 'Error';
            const statusClass = log.success ? 'status-success' : 'status-error';
            
            row.innerHTML = `
                <td>${timestamp}</td>
                <td>${log.database_type}</td>
                <td>${log.user}</td>
                <td>${log.operation}</td>
                <td><span class="${statusClass}">${status}</span></td>
            `;
            
            tbody.appendChild(row);
        });
    }

    updateThreatsTable(threats) {
        const tbody = document.getElementById('threats-tbody');
        tbody.innerHTML = '';
        
        threats.slice(-20).reverse().forEach(threat => {
            const row = document.createElement('tr');
            const timestamp = new Date(threat.timestamp).toLocaleTimeString();
            const severityClass = `severity-${threat.severity}`;
            
            row.innerHTML = `
                <td>${timestamp}</td>
                <td>${threat.type.replace(/_/g, ' ')}</td>
                <td><span class="${severityClass}">${threat.severity}</span></td>
                <td>${threat.description}</td>
            `;
            
            tbody.appendChild(row);
        });
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    new DatabaseAuditDashboard();
});

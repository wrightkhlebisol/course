// Dashboard JavaScript for Azure Monitor Integration
let socket;
let logTypesChart;
let timelineChart;
let currentStats = {};
let timelineData = [];
let timelineLabels = [];

function initializeDashboard(stats, insights) {
    console.log('🚀 Initializing Azure Monitor Dashboard');
    
    // Store initial stats
    currentStats = { ...stats };
    
    // Initialize timeline data
    initializeTimelineData();
    
    // Setup WebSocket connection
    setupWebSocket();
    
    // Initialize charts
    setupCharts(stats);
    
    // Load recent logs
    loadRecentLogs();
    
    // Setup auto-refresh every 10 seconds for more real-time feel
    setInterval(updateDashboard, 10000);
}

function initializeTimelineData() {
    const now = new Date();
    timelineLabels = [];
    timelineData = [];
    
    for (let i = 29; i >= 0; i--) {
        const time = new Date(now.getTime() - i * 60000);
        timelineLabels.push(time.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}));
        timelineData.push(0);
    }
}

function setupWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    socket = new WebSocket(wsUrl);
    
    socket.onopen = function(event) {
        console.log('✅ WebSocket connected');
        updateConnectionStatus(true);
    };
    
    socket.onmessage = function(event) {
        try {
            const message = JSON.parse(event.data);
            
            if (message.type === 'new_log') {
                addNewLogToTable(message.data);
                updateMetrics(message.stats, true);
                updateCharts(message.stats);
                updateTimelineData();
            } else if (message.type === 'stats_update') {
                updateMetrics(message.stats, true);
                updateCharts(message.stats);
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    };
    
    socket.onclose = function(event) {
        console.log('❌ WebSocket disconnected');
        updateConnectionStatus(false);
        // Attempt to reconnect after 5 seconds
        setTimeout(setupWebSocket, 5000);
    };
    
    socket.onerror = function(error) {
        console.error('WebSocket error:', error);
        updateConnectionStatus(false);
    };
}

function updateConnectionStatus(connected) {
    const statusIndicator = document.querySelector('.status-indicator');
    const statusText = statusIndicator?.nextElementSibling;
    
    if (statusIndicator) {
        statusIndicator.className = connected ? 'status-indicator healthy' : 'status-indicator unhealthy';
    }
    
    if (statusText) {
        statusText.textContent = connected ? 'Connected' : 'Disconnected';
    }
}

function setupCharts(stats) {
    // Log Types Pie Chart
    const logTypesCtx = document.getElementById('logTypesChart').getContext('2d');
    logTypesChart = new Chart(logTypesCtx, {
        type: 'pie',
        data: {
            labels: ['App Traces', 'Security Events', 'Performance'],
            datasets: [{
                data: [
                    stats.table_AppTraces || 0,
                    stats.table_SecurityEvent || 0,
                    stats.table_Perf || 0
                ],
                backgroundColor: [
                    '#2a5298',
                    '#dc3545',
                    '#ff9800'
                ],
                borderWidth: 3,
                borderColor: '#ffffff',
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: {
                            size: 13,
                            weight: '600'
                        },
                        color: '#495057'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        size: 14,
                        weight: '600'
                    },
                    bodyFont: {
                        size: 13
                    },
                    borderColor: '#2a5298',
                    borderWidth: 2
                }
            },
            animation: {
                animateRotate: true,
                animateScale: true
            }
        }
    });
    
    // Timeline Chart
    const timelineCtx = document.getElementById('timelineChart').getContext('2d');
    timelineChart = new Chart(timelineCtx, {
        type: 'line',
        data: {
            labels: timelineLabels,
            datasets: [{
                label: 'Logs per Minute',
                data: timelineData,
                borderColor: '#2a5298',
                backgroundColor: 'rgba(42, 82, 152, 0.15)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointBackgroundColor: '#2a5298',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        color: '#6c757d',
                        font: {
                            size: 12
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#6c757d',
                        font: {
                            size: 11
                        },
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: {
                        size: 14,
                        weight: '600'
                    },
                    bodyFont: {
                        size: 13
                    },
                    borderColor: '#2a5298',
                    borderWidth: 2
                }
            },
            animation: {
                duration: 750
            }
        }
    });
}

function updateTimelineData() {
    if (timelineChart) {
        // Shift data left
        timelineData.shift();
        // Add new data point (use a sample value, ideally from stats)
        const newValue = Math.floor(Math.random() * 25) + 5;
        timelineData.push(newValue);
        
        // Update labels if needed
        const now = new Date();
        timelineLabels.shift();
        timelineLabels.push(now.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}));
        
        timelineChart.data.labels = [...timelineLabels];
        timelineChart.data.datasets[0].data = [...timelineData];
        timelineChart.update('active');
    }
}

function addNewLogToTable(logEntry) {
    const tbody = document.getElementById('logsTableBody');
    const row = document.createElement('tr');
    row.className = 'new-row';
    
    const timestamp = new Date(logEntry.timestamp).toLocaleString();
    const levelClass = `level-${logEntry.level}`;
    
    // Escape HTML to prevent XSS
    const escapeHtml = (text) => {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };
    
    row.innerHTML = `
        <td>${escapeHtml(timestamp)}</td>
        <td>${escapeHtml(logEntry.workspace || 'N/A')}</td>
        <td>${escapeHtml(logEntry.table || 'N/A')}</td>
        <td class="${levelClass}">${escapeHtml(logEntry.level || 'INFO')}</td>
        <td>${escapeHtml(logEntry.message || 'N/A')}</td>
        <td>${escapeHtml(logEntry.resource || 'N/A')}</td>
    `;
    
    // Add to top of table
    tbody.insertBefore(row, tbody.firstChild);
    
    // Keep only last 50 rows
    while (tbody.children.length > 50) {
        tbody.removeChild(tbody.lastChild);
    }
}

function animateValue(element, start, end, duration = 600) {
    const startTime = performance.now();
    const difference = end - start;
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function for smooth animation
        const easeOutCubic = 1 - Math.pow(1 - progress, 3);
        const current = Math.floor(start + difference * easeOutCubic);
        
        element.textContent = current.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            element.textContent = end.toLocaleString();
        }
    }
    
    requestAnimationFrame(update);
}

function updateMetrics(stats, animate = false) {
    const metricElements = {
        'total_processed': stats.total_processed || 0,
        'security_incidents': stats.security_incidents || 0,
        'application_errors': stats.application_errors || 0,
        'performance_alerts': stats.performance_alerts || 0
    };
    
    Object.entries(metricElements).forEach(([key, newValue]) => {
        const element = document.querySelector(`.metric-value[data-metric="${key}"]`);
        if (element) {
            const oldValue = currentStats[key] || 0;
            const metricCard = element.closest('.metric-card');
            
            if (oldValue !== newValue && animate) {
                // Add update animation
                element.classList.add('updated');
                if (metricCard) {
                    metricCard.classList.add('updating');
                    
                    // Remove animation classes after animation completes
                    setTimeout(() => {
                        element.classList.remove('updated');
                        metricCard.classList.remove('updating');
                    }, 600);
                }
                
                // Animate value change
                animateValue(element, oldValue, newValue);
            } else {
                element.textContent = newValue.toLocaleString();
            }
            
            // Add change indicator
            if (oldValue < newValue && metricCard) {
                const indicator = document.createElement('div');
                indicator.className = 'metric-change-indicator';
                indicator.style.position = 'absolute';
                indicator.style.top = '15px';
                indicator.style.right = '15px';
                indicator.style.width = '8px';
                indicator.style.height = '8px';
                indicator.style.borderRadius = '50%';
                indicator.style.background = '#28a745';
                metricCard.appendChild(indicator);
                
                setTimeout(() => {
                    indicator.remove();
                }, 1000);
            }
        }
    });
    
    // Update current stats
    currentStats = { ...stats };
}

function updateCharts(stats) {
    // Update pie chart
    if (logTypesChart) {
        const oldData = logTypesChart.data.datasets[0].data;
        const newData = [
            stats.table_AppTraces || 0,
            stats.table_SecurityEvent || 0,
            stats.table_Perf || 0
        ];
        
        // Only update if data changed
        if (JSON.stringify(oldData) !== JSON.stringify(newData)) {
            logTypesChart.data.datasets[0].data = newData;
            logTypesChart.update('active');
        }
    }
    
    // Timeline chart is updated separately via updateTimelineData()
}

async function loadRecentLogs() {
    try {
        const response = await fetch('/api/recent-logs');
        const logs = await response.json();
        
        const tbody = document.getElementById('logsTableBody');
        tbody.innerHTML = '';
        
        logs.forEach(log => {
            const row = document.createElement('tr');
            const timestamp = new Date(log.timestamp).toLocaleString();
            const levelClass = `level-${log.level}`;
            
            // Escape HTML
            const escapeHtml = (text) => {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            };
            
            row.innerHTML = `
                <td>${escapeHtml(timestamp)}</td>
                <td>${escapeHtml(log.workspace || 'N/A')}</td>
                <td>${escapeHtml(log.table || 'N/A')}</td>
                <td class="${levelClass}">${escapeHtml(log.level || 'INFO')}</td>
                <td>${escapeHtml(log.message || 'N/A')}</td>
                <td>${escapeHtml(log.resource || 'N/A')}</td>
            `;
            
            tbody.appendChild(row);
        });
        
    } catch (error) {
        console.error('Failed to load recent logs:', error);
    }
}

async function updateDashboard() {
    try {
        // Update stats
        const statsResponse = await fetch('/api/stats');
        const stats = await statsResponse.json();
        
        // Update insights
        const insightsResponse = await fetch('/api/insights');
        const insights = await insightsResponse.json();
        
        // Update last update time
        const lastUpdateElement = document.getElementById('lastUpdate');
        if (lastUpdateElement && insights.last_processed) {
            lastUpdateElement.textContent = new Date(insights.last_processed).toLocaleString();
        }
        
        // Update metrics with animation if values changed
        updateMetrics(stats, true);
        updateCharts(stats);
        
        // Update workspace count if available
        const workspaceElement = document.querySelector('.insight-item strong')?.parentElement?.querySelector('span');
        if (workspaceElement && insights.workspaces_active !== undefined) {
            workspaceElement.textContent = insights.workspaces_active;
        }
        
    } catch (error) {
        console.error('Failed to update dashboard:', error);
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Dashboard will be initialized by inline script with server data
});

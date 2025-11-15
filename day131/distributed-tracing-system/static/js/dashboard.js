class TracingDashboard {
    constructor() {
        this.socket = null;
        this.traces = [];
        this.selectedTraceId = null;
        this.performanceChart = null;
        this.init();
    }

    async init() {
        this.setupWebSocket();
        this.setupEventListeners();
        this.initPerformanceChart();
        await this.loadInitialData();
        this.startPeriodicUpdates();
    }

    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = () => {
            console.log('WebSocket connected');
            this.updateConnectionStatus(true);
        };
        
        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.socket.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateConnectionStatus(false);
            // Attempt to reconnect after 5 seconds
            setTimeout(() => this.setupWebSocket(), 5000);
        };
        
        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateConnectionStatus(false);
        };
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'traces_update':
                this.traces = data.data || [];
                this.updateTraceTimeline();
                this.updateMetrics();
                this.updateServiceMap();
                break;
            case 'new_trace':
                this.traces.unshift(data.data);
                this.traces = this.traces.slice(0, 100); // Keep last 100 traces
                this.updateTraceTimeline();
                this.updateMetrics();
                this.updateServiceMap();
                this.addActivityLog(`New trace: ${data.data.trace_id}`);
                break;
        }
    }

    updateConnectionStatus(isConnected) {
        const statusDot = document.getElementById('connection-status');
        if (statusDot) {
            statusDot.className = `status-dot ${isConnected ? 'online' : 'offline'}`;
        }
    }

    setupEventListeners() {
        // Add event listeners for trace selection
        document.addEventListener('click', (event) => {
            if (event.target.closest('.trace-item')) {
                const traceItem = event.target.closest('.trace-item');
                const traceId = traceItem.dataset.traceId;
                this.selectTrace(traceId);
            }
        });
    }

    async loadInitialData() {
        try {
            console.log('Loading initial trace data...');
            const response = await fetch('/api/traces');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log('Loaded traces:', data.traces?.length || 0);
            this.traces = data.traces || [];
            this.updateTraceTimeline();
            this.updateMetrics();
            this.updateServiceMap();
            if (this.traces.length > 0) {
                this.addActivityLog(`Loaded ${this.traces.length} traces`);
            }
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.addActivityLog(`Failed to load trace data: ${error.message}`, 'error');
        }
    }

    updateTraceTimeline() {
        const timeline = document.getElementById('trace-timeline');
        if (!timeline) return;

        if (this.traces.length === 0) {
            timeline.innerHTML = '<p class="no-data">No traces available</p>';
            return;
        }

        const traceItems = this.traces.slice(0, 20).map(trace => {
            const errorClass = trace.error_count > 0 ? 'error' : '';
            const duration = Math.round(trace.total_duration_ms);
            const services = trace.services.join(', ');
            
            return `
                <div class="trace-item ${errorClass}" data-trace-id="${trace.trace_id}">
                    <div class="trace-info">
                        <div class="trace-id">🔍 ${trace.trace_id.substring(0, 8)}...</div>
                        <div class="trace-meta">
                            <span>⏱️ ${duration}ms</span>
                            <span>🔗 ${trace.span_count} spans</span>
                            <span>🏢 ${services}</span>
                            ${trace.error_count > 0 ? `<span style="color: #ef4444;">❌ ${trace.error_count} errors</span>` : ''}
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        timeline.innerHTML = traceItems;
    }

    updateMetrics() {
        const totalTraces = this.traces.length;
        const avgDuration = totalTraces > 0 
            ? Math.round(this.traces.reduce((sum, trace) => sum + (trace.total_duration_ms || 0), 0) / totalTraces)
            : 0;
        
        const errorTraces = this.traces.filter(trace => trace.error_count > 0).length;
        const errorRate = totalTraces > 0 ? Math.round((errorTraces / totalTraces) * 100) : 0;
        
        const allServices = new Set();
        this.traces.forEach(trace => {
            if (trace.services && Array.isArray(trace.services)) {
                trace.services.forEach(service => allServices.add(service));
            }
        });

        console.log('Updating metrics:', { totalTraces, avgDuration, errorRate, activeServices: allServices.size });

        this.updateMetricCard('total-traces', totalTraces);
        this.updateMetricCard('avg-duration', `${avgDuration}ms`);
        this.updateMetricCard('error-rate', `${errorRate}%`);
        this.updateMetricCard('active-services', allServices.size);

        // Update performance chart and service map
        this.updatePerformanceChart();
        this.updateServiceMap();
    }

    updateMetricCard(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    async selectTrace(traceId) {
        this.selectedTraceId = traceId;
        
        try {
            const response = await fetch(`/api/trace/${traceId}`);
            const data = await response.json();
            this.displayTraceDetails(data);
            this.addActivityLog(`Selected trace: ${traceId}`);
        } catch (error) {
            console.error('Failed to load trace details:', error);
            this.addActivityLog(`Failed to load trace details: ${traceId}`, 'error');
        }
    }

    displayTraceDetails(traceData) {
        const detailsContainer = document.getElementById('trace-details');
        if (!detailsContainer) return;

        const spans = traceData.spans || [];
        if (spans.length === 0) {
            detailsContainer.innerHTML = '<p class="no-data">No span data available</p>';
            return;
        }

        // Sort spans by start time
        spans.sort((a, b) => a.start_time - b.start_time);

        const spanItems = spans.map(span => {
            const errorClass = span.status === 'error' ? 'error' : '';
            const duration = Math.round(span.duration_ms);
            
            return `
                <div class="span-item ${errorClass}">
                    <div class="span-header">
                        <div class="span-operation">${span.operation}</div>
                        <div class="span-duration">${duration}ms</div>
                    </div>
                    <div class="span-service">${span.service_name}</div>
                    ${span.status === 'error' ? `<div style="color: #ef4444; font-size: 0.8rem;">Error: ${span.metadata?.error || 'Unknown error'}</div>` : ''}
                </div>
            `;
        }).join('');

        detailsContainer.innerHTML = `
            <div class="trace-summary">
                <h4>Trace: ${traceData.trace_id.substring(0, 16)}...</h4>
                <p>${spans.length} spans across ${new Set(spans.map(s => s.service_name)).size} services</p>
            </div>
            <div class="spans-list">
                ${spanItems}
            </div>
        `;
    }

    initPerformanceChart() {
        const ctx = document.getElementById('performance-chart');
        if (!ctx) return;

        this.performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Average Response Time (ms)',
                    data: [],
                    borderColor: '#0d9488',
                    backgroundColor: 'rgba(13, 148, 136, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'Error Rate (%)',
                    data: [],
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Response Time (ms)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Error Rate (%)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                }
            }
        });
    }

    updatePerformanceChart() {
        if (!this.performanceChart || this.traces.length === 0) return;

        // Group traces by minute
        const now = Date.now() / 1000;
        const timeWindows = {};
        
        this.traces.forEach(trace => {
            const timeKey = Math.floor(trace.start_time / 60) * 60; // Round to minute
            if (now - timeKey < 3600) { // Last hour only
                if (!timeWindows[timeKey]) {
                    timeWindows[timeKey] = { durations: [], errors: 0, total: 0 };
                }
                timeWindows[timeKey].durations.push(trace.total_duration_ms);
                timeWindows[timeKey].total++;
                if (trace.error_count > 0) {
                    timeWindows[timeKey].errors++;
                }
            }
        });

        const sortedTimes = Object.keys(timeWindows).sort();
        const labels = sortedTimes.map(time => {
            const date = new Date(parseInt(time) * 1000);
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        });

        const avgDurations = sortedTimes.map(time => {
            const window = timeWindows[time];
            return window.durations.reduce((sum, d) => sum + d, 0) / window.durations.length;
        });

        const errorRates = sortedTimes.map(time => {
            const window = timeWindows[time];
            return (window.errors / window.total) * 100;
        });

        this.performanceChart.data.labels = labels;
        this.performanceChart.data.datasets[0].data = avgDurations;
        this.performanceChart.data.datasets[1].data = errorRates;
        this.performanceChart.update('none');
    }

    addActivityLog(message, level = 'info') {
        const logContainer = document.getElementById('activity-log');
        if (!logContainer) return;

        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${level}`;
        logEntry.innerHTML = `
            <div class="log-timestamp">${timestamp}</div>
            <div>${message}</div>
        `;

        logContainer.insertBefore(logEntry, logContainer.firstChild);

        // Keep only last 50 log entries
        while (logContainer.children.length > 50) {
            logContainer.removeChild(logContainer.lastChild);
        }
    }

    async updateServiceMap() {
        const serviceMapContainer = document.getElementById('service-map');
        if (!serviceMapContainer) return;

        if (this.traces.length === 0) {
            serviceMapContainer.innerHTML = '<p class="no-data">No service data available. Generate some traces first.</p>';
            return;
        }

        // Build service dependency graph from trace data
        const serviceDeps = new Map(); // service -> Set of services it calls
        const serviceStats = new Map(); // service -> { calls: count, errors: count }
        
        // Load detailed trace data for dependency analysis
        const tracePromises = this.traces.slice(0, 10).map(trace => 
            fetch(`/api/trace/${trace.trace_id}`).then(r => r.json()).catch(() => null)
        );
        
        const traceDetails = await Promise.all(tracePromises);
        
        traceDetails.forEach(traceData => {
            if (!traceData || !traceData.spans) return;
            
            const spans = traceData.spans;
            const spanMap = new Map(); // span_id -> span
            spans.forEach(span => {
                spanMap.set(span.span_id, span);
                
                // Initialize service stats
                if (!serviceStats.has(span.service_name)) {
                    serviceStats.set(span.service_name, { calls: 0, errors: 0 });
                }
                const stats = serviceStats.get(span.service_name);
                stats.calls++;
                if (span.status === 'error') {
                    stats.errors++;
                }
            });
            
            // Build dependencies from parent-child relationships
            spans.forEach(span => {
                if (span.parent_span_id) {
                    const parentSpan = spanMap.get(span.parent_span_id);
                    if (parentSpan && parentSpan.service_name !== span.service_name) {
                        // Parent service calls this service
                        if (!serviceDeps.has(parentSpan.service_name)) {
                            serviceDeps.set(parentSpan.service_name, new Set());
                        }
                        serviceDeps.get(parentSpan.service_name).add(span.service_name);
                    }
                }
            });
        });

        // If no dependencies found, show services that appear together in traces
        if (serviceDeps.size === 0) {
            this.traces.forEach(trace => {
                if (trace.services && trace.services.length > 1) {
                    for (let i = 0; i < trace.services.length; i++) {
                        for (let j = i + 1; j < trace.services.length; j++) {
                            const service1 = trace.services[i];
                            const service2 = trace.services[j];
                            if (!serviceDeps.has(service1)) {
                                serviceDeps.set(service1, new Set());
                            }
                            serviceDeps.get(service1).add(service2);
                        }
                    }
                }
            });
        }

        // Render service map
        const allServices = Array.from(new Set([
            ...Array.from(serviceDeps.keys()),
            ...Array.from(serviceDeps.values()).flatMap(s => Array.from(s))
        ]));

        if (allServices.length === 0) {
            serviceMapContainer.innerHTML = '<p class="no-data">No services detected in traces</p>';
            return;
        }

        const serviceColors = {
            'api-gateway': '#0d9488',
            'user-service': '#10b981',
            'database-service': '#f59e0b',
            'tracing-dashboard': '#14b8a6'
        };

        const getServiceColor = (service) => {
            return serviceColors[service] || '#718096';
        };

        let html = '<div class="service-map-graph">';
        
        // Render services as nodes
        allServices.forEach(service => {
            const stats = serviceStats.get(service) || { calls: 0, errors: 0 };
            const color = getServiceColor(service);
            const errorRate = stats.calls > 0 ? Math.round((stats.errors / stats.calls) * 100) : 0;
            
            html += `
                <div class="service-node" style="border-color: ${color};">
                    <div class="service-name" style="color: ${color};">${service}</div>
                    <div class="service-stats">
                        <span>📊 ${stats.calls} calls</span>
                        ${errorRate > 0 ? `<span style="color: #ef4444;">❌ ${errorRate}% errors</span>` : ''}
                    </div>
                </div>
            `;
        });

        // Render dependencies as connections
        if (serviceDeps.size > 0) {
            html += '<div class="service-connections">';
            serviceDeps.forEach((targets, source) => {
                targets.forEach(target => {
                    const sourceColor = getServiceColor(source);
                    html += `
                        <div class="service-connection" style="border-color: ${sourceColor};">
                            <span class="connection-source">${source}</span>
                            <span class="connection-arrow">→</span>
                            <span class="connection-target">${target}</span>
                        </div>
                    `;
                });
            });
            html += '</div>';
        }

        html += '</div>';
        serviceMapContainer.innerHTML = html;
    }

    startPeriodicUpdates() {
        // Update dashboard every 30 seconds as fallback
        setInterval(async () => {
            if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
                await this.loadInitialData();
            }
        }, 30000);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new TracingDashboard();
});

import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import requests
import time
import os
from datetime import datetime, timedelta
import dash_bootstrap_components as dbc

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
])

# API base URL - configurable via environment variable
API_BASE = os.getenv('API_BASE_URL', 'http://localhost:8001')

def create_layout():
    return html.Div([
        # Top Navigation Bar (Google-style)
        dbc.Navbar(
            dbc.Container([
                dbc.NavbarBrand([
                    html.I(className="fas fa-filter me-2"),
                    "Bloom Filter Log Analytics"
                ], className="fw-bold fs-4"),
                dbc.Nav([
                    dbc.NavItem(dbc.NavLink("Dashboard", href="#", active=True)),
                    dbc.NavItem(dbc.NavLink("API Docs", href="http://localhost:8001/docs", target="_blank")),
                ]),
                dbc.Nav([
                    dbc.Button("🔄 Refresh", id="refresh-btn", color="outline-light", size="sm", className="me-2"),
                    dbc.Button("📊 Stats", id="stats-btn", color="outline-light", size="sm"),
                ])
            ]),
            color="primary",
            dark=True,
            className="mb-4"
        ),
        
        # Main Content Container
        dbc.Container([
            # Top Stats Cards Row
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="fas fa-database text-primary fs-1 me-3"),
                                html.Div([
                                    html.H4("Total Filters", className="mb-0"),
                                    html.H2(id="total-filters", children="3", className="text-primary mb-0")
                                ])
                            ], className="d-flex align-items-center")
                        ])
                    ], className="h-100 border-0 shadow-sm")
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="fas fa-chart-line text-success fs-1 me-3"),
                                html.Div([
                                    html.H4("Avg Performance", className="mb-0"),
                                    html.H2(id="avg-performance", children="0.5ms", className="text-success mb-0")
                                ])
                            ], className="d-flex align-items-center")
                        ])
                    ], className="h-100 border-0 shadow-sm")
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="fas fa-exclamation-triangle text-warning fs-1 me-3"),
                                html.Div([
                                    html.H4("False Positives", className="mb-0"),
                                    html.H2(id="false-positives", children="2.1%", className="text-warning mb-0")
                                ])
                            ], className="d-flex align-items-center")
                        ])
                    ], className="h-100 border-0 shadow-sm")
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.I(className="fas fa-memory text-info fs-1 me-3"),
                                html.Div([
                                    html.H4("Memory Usage", className="mb-0"),
                                    html.H2(id="memory-usage", children="45KB", className="text-info mb-0")
                                ])
                            ], className="d-flex align-items-center")
                        ])
                    ], className="h-100 border-0 shadow-sm")
                ], width=3),
            ], className="mb-4"),
            
            # Main Content Row
            dbc.Row([
                # Left Sidebar - Controls
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5("🎛️ Control Panel", className="mb-0 text-primary")
                        ], className="bg-light"),
                        dbc.CardBody([
                            # Quick Actions
                            html.H6("Quick Actions", className="text-muted mb-3"),
                            dbc.Row([
                                dbc.Col(dbc.Button("📊 Populate Demo Data", id="populate-btn", 
                                                  color="primary", className="w-100 mb-2"), width=12),
                                dbc.Col(dbc.Button("⚡ Performance Test", id="performance-btn", 
                                                  color="success", className="w-100 mb-2"), width=12),
                            ], className="mb-4"),
                            
                            # Add Log Entry
                            html.H6("➕ Add Log Entry", className="text-muted mb-3"),
                            dbc.Select(
                                id='log-type-dropdown',
                                options=[
                                    {'label': '🔴 Error Logs', 'value': 'error_logs'},
                                    {'label': '🔵 Access Logs', 'value': 'access_logs'},
                                    {'label': '🛡️ Security Logs', 'value': 'security_logs'}
                                ],
                                value='error_logs',
                                className="mb-3"
                            ),
                            dbc.Input(
                                id='log-key-input',
                                type='text',
                                placeholder='Enter log key...',
                                className="mb-3"
                            ),
                            dbc.Button("Add Entry", id="add-entry-btn", color="success", className="w-100 mb-4"),
                            
                            # Query Log Entry
                            html.H6("🔍 Query Log Entry", className="text-muted mb-3"),
                            dbc.Select(
                                id='query-type-dropdown',
                                options=[
                                    {'label': '🔴 Error Logs', 'value': 'error_logs'},
                                    {'label': '🔵 Access Logs', 'value': 'access_logs'},
                                    {'label': '🛡️ Security Logs', 'value': 'security_logs'}
                                ],
                                value='error_logs',
                                className="mb-3"
                            ),
                            dbc.Input(
                                id='query-key-input',
                                type='text',
                                placeholder='Enter log key to search...',
                                className="mb-3"
                            ),
                            dbc.Button("Query", id="query-btn", color="info", className="w-100"),
                        ])
                    ], className="h-100 border-0 shadow-sm")
                ], width=3),
                
                # Main Content Area
                dbc.Col([
                    # Results Panel
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5("📋 Results", className="mb-0 text-primary")
                        ], className="bg-light"),
                        dbc.CardBody([
                            html.Div(id="results-panel", children=[
                                html.Div([
                                    html.I(className="fas fa-info-circle text-muted me-2"),
                                    "Use the control panel to interact with bloom filters."
                                ], className="text-muted text-center py-4")
                            ])
                        ])
                    ], className="mb-4 border-0 shadow-sm"),
                    
                    # Charts Row
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.H5("📈 False Positive Rates", className="mb-0 text-primary")
                                ], className="bg-light"),
                                dbc.CardBody([
                                    dcc.Graph(id="false-positive-chart", style={'height': '300px'})
                                ])
                            ], className="h-100 border-0 shadow-sm")
                        ], width=6),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader([
                                    html.H5("💾 Memory Usage", className="mb-0 text-primary")
                                ], className="bg-light"),
                                dbc.CardBody([
                                    dcc.Graph(id="memory-usage-chart", style={'height': '300px'})
                                ])
                            ], className="h-100 border-0 shadow-sm")
                        ], width=6),
                    ], className="mb-4"),
                    
                    # Performance Chart
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5("⚡ Performance Comparison", className="mb-0 text-primary")
                        ], className="bg-light"),
                        dbc.CardBody([
                            dcc.Graph(id="performance-comparison-chart", style={'height': '400px'})
                        ])
                    ], className="border-0 shadow-sm")
                ], width=9),
            ]),
            
            # Filter Statistics Cards (Auto-generated)
            html.Div(id="stats-cards", className="mt-4"),
            
        ], fluid=True),
        
        # Auto-refresh interval
        dcc.Interval(
            id='interval-component',
            interval=5*1000,  # in milliseconds
            n_intervals=0
        ),
        
        # Hidden div to store data
        html.Div(id='hidden-div', style={'display': 'none'})
    ])

app.layout = create_layout()

# Callbacks
@app.callback(
    Output('results-panel', 'children'),
    [Input('populate-btn', 'n_clicks'),
     Input('performance-btn', 'n_clicks'),
     Input('add-entry-btn', 'n_clicks'),
     Input('query-btn', 'n_clicks')],
    [State('log-type-dropdown', 'value'),
     State('log-key-input', 'value'),
     State('query-type-dropdown', 'value'),
     State('query-key-input', 'value')]
)
def handle_button_clicks(populate_clicks, performance_clicks, add_clicks, query_clicks,
                        log_type, log_key, query_type, query_key):
    ctx = callback_context
    if not ctx.triggered:
        return html.Div([
            html.I(className="fas fa-info-circle text-muted me-2"),
            "Use the control panel to interact with bloom filters."
        ], className="text-muted text-center py-4")
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        if button_id == 'populate-btn' and populate_clicks:
            response = requests.post(f"{API_BASE}/demo/populate", params={"count": 10000})
            if response.status_code == 200:
                data = response.json()
                return dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-check-circle text-success fs-1 me-3"),
                            html.Div([
                                html.H4("✅ Demo Data Populated Successfully", className="text-success mb-2"),
                                html.P(f"📊 Records added: {data['records_added']:,}", className="mb-1"),
                                html.P(f"🔧 Filters populated: {', '.join(data['filters_populated'])}", className="mb-0")
                            ])
                        ], className="d-flex align-items-center")
                    ])
                ], className="border-0 shadow-sm bg-success bg-opacity-10")
        
        elif button_id == 'performance-btn' and performance_clicks:
            response = requests.post(f"{API_BASE}/demo/performance-test")
            if response.status_code == 200:
                data = response.json()
                return dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-rocket text-primary fs-1 me-3"),
                            html.Div([
                                html.H4("🚀 Performance Test Results", className="text-primary mb-3"),
                                dbc.Row([
                                    dbc.Col([
                                        html.Div([
                                            html.Small("Bloom Filter", className="text-muted"),
                                            html.H5(f"{data['bloom_filter_performance']['avg_time_per_query_ms']:.3f} ms/query", className="text-success mb-0")
                                        ])
                                    ], width=6),
                                    dbc.Col([
                                        html.Div([
                                            html.Small("Traditional", className="text-muted"),
                                            html.H5(f"{data['traditional_lookup_performance']['avg_time_per_query_ms']:.1f} ms/query", className="text-warning mb-0")
                                        ])
                                    ], width=6),
                                ], className="mb-3"),
                                dbc.Row([
                                    dbc.Col([
                                        html.Div([
                                            html.Small("Speed Improvement", className="text-muted"),
                                            html.H5(f"{data['speed_improvement']['times_faster']:.0f}x faster", className="text-info mb-0")
                                        ])
                                    ], width=6),
                                    dbc.Col([
                                        html.Div([
                                            html.Small("False Positive Rate", className="text-muted"),
                                            html.H5(f"{data['accuracy_metrics']['false_positive_rate']:.1%}", className="text-warning mb-0")
                                        ])
                                    ], width=6),
                                ])
                            ])
                        ], className="d-flex align-items-start")
                    ])
                ], className="border-0 shadow-sm bg-primary bg-opacity-10")
        
        elif button_id == 'add-entry-btn' and add_clicks and log_key:
            response = requests.post(f"{API_BASE}/logs/add", 
                                   json={"log_type": log_type, "log_key": log_key})
            if response.status_code == 200:
                data = response.json()
                return dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="fas fa-plus-circle text-success fs-1 me-3"),
                            html.Div([
                                html.H4("✅ Log Entry Added Successfully", className="text-success mb-2"),
                                html.P(f"📝 Type: {data['log_type'].replace('_', ' ').title()}", className="mb-1"),
                                html.P(f"🔑 Key: {data['log_key']}", className="mb-1"),
                                html.P(f"⚡ Processing time: {data['processing_time_ms']:.3f} ms", className="mb-0")
                            ])
                        ], className="d-flex align-items-center")
                    ])
                ], className="border-0 shadow-sm bg-success bg-opacity-10")
        
        elif button_id == 'query-btn' and query_clicks and query_key:
            response = requests.post(f"{API_BASE}/logs/query",
                                   json={"log_type": query_type, "log_key": query_key})
            if response.status_code == 200:
                data = response.json()
                if data['might_exist']:
                    icon_class = "fas fa-search text-warning"
                    title_class = "text-warning"
                    bg_class = "bg-warning bg-opacity-10"
                    confidence_text = "Probably exists (may be false positive)"
                else:
                    icon_class = "fas fa-times-circle text-danger"
                    title_class = "text-danger"
                    bg_class = "bg-danger bg-opacity-10"
                    confidence_text = "Definitely not exist (100% accurate)"
                
                return dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className=f"{icon_class} fs-1 me-3"),
                            html.Div([
                                html.H4(f"🔍 Query Result", className=f"{title_class} mb-2"),
                                html.P(f"🔑 Key: {data['log_key']}", className="mb-1"),
                                html.P(f"📊 Result: {confidence_text}", className="mb-1"),
                                html.P(f"⚡ Processing time: {data['processing_time_ms']:.3f} ms", className="mb-0"),
                                html.Small("Note: 'Probably exists' may be false positive, 'Definitely not exist' is 100% accurate.",
                                          className="text-muted fst-italic")
                            ])
                        ], className="d-flex align-items-start")
                    ])
                ], className=f"border-0 shadow-sm {bg_class}")
    
    except requests.RequestException as e:
        return dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.I(className="fas fa-exclamation-triangle text-danger fs-1 me-3"),
                    html.Div([
                        html.H4("❌ Connection Error", className="text-danger mb-2"),
                        html.P(f"Failed to connect to API: {str(e)}", className="mb-1"),
                        html.P("Make sure the API server is running on port 8001.", className="mb-0")
                    ])
                ], className="d-flex align-items-center")
            ])
        ], className="border-0 shadow-sm bg-danger bg-opacity-10")
    
    return html.Div([
        html.I(className="fas fa-info-circle text-muted me-2"),
        "No action performed."
    ], className="text-muted text-center py-4")

@app.callback(
    [Output('stats-cards', 'children'),
     Output('false-positive-chart', 'figure'),
     Output('memory-usage-chart', 'figure'),
     Output('total-filters', 'children'),
     Output('avg-performance', 'children'),
     Output('false-positives', 'children'),
     Output('memory-usage', 'children')],
    [Input('interval-component', 'n_intervals'),
     Input('refresh-btn', 'n_clicks'),
     Input('stats-btn', 'n_clicks')]
)
def update_dashboard(n_intervals, refresh_clicks, stats_clicks):
    try:
        response = requests.get(f"{API_BASE}/stats")
        if response.status_code != 200:
            raise requests.RequestException("API not available")
        
        stats = response.json()
        
        # Calculate summary stats for top cards
        total_filters = len(stats)
        avg_false_positive = sum(filter_stats['current_false_positive_rate'] for filter_stats in stats.values()) / total_filters if total_filters > 0 else 0
        total_memory = sum(filter_stats['memory_usage_bytes'] for filter_stats in stats.values()) / 1024  # KB
        
        # Create detailed stats cards with Google-style design
        cards = []
        filter_names = []
        false_positive_rates = []
        memory_usage = []
        
        for filter_name, filter_stats in stats.items():
            filter_names.append(filter_name.replace('_', ' ').title())
            false_positive_rates.append(filter_stats['current_false_positive_rate'] * 100)
            memory_usage.append(filter_stats['memory_usage_bytes'] / 1024)  # Convert to KB
            
            # Determine status color based on false positive rate
            fp_rate = filter_stats['current_false_positive_rate']
            if fp_rate < 0.01:
                status_color = "success"
                status_icon = "fas fa-check-circle"
            elif fp_rate < 0.05:
                status_color = "warning"
                status_icon = "fas fa-exclamation-triangle"
            else:
                status_color = "danger"
                status_icon = "fas fa-times-circle"
            
            cards.append(
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.I(className=f"{status_icon} text-{status_color} me-2"),
                            html.H6(filter_name.replace('_', ' ').title(), className="mb-0")
                        ], className="d-flex align-items-center")
                    ], className="bg-light"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.Small("Elements", className="text-muted"),
                                    html.H5(f"{filter_stats['elements_added']:,}", className="mb-0")
                                ])
                            ], width=6),
                            dbc.Col([
                                html.Div([
                                    html.Small("Queries", className="text-muted"),
                                    html.H5(f"{filter_stats['queries_made']:,}", className="mb-0")
                                ])
                            ], width=6),
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.Small("False Positive", className="text-muted"),
                                    html.H6(f"{filter_stats['current_false_positive_rate']:.2%}", 
                                           className=f"text-{status_color} mb-0")
                                ])
                            ], width=6),
                            dbc.Col([
                                html.Div([
                                    html.Small("Memory", className="text-muted"),
                                    html.H6(f"{filter_stats['memory_usage_bytes']/1024:.1f} KB", className="mb-0")
                                ])
                            ], width=6),
                        ])
                    ])
                ], className="mb-3 border-0 shadow-sm")
            )
        
        # False positive rate chart
        fp_fig = go.Figure(data=[
            go.Bar(x=filter_names, y=false_positive_rates, 
                   marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1'],
                   hovertemplate='<b>%{x}</b><br>False Positive Rate: %{y:.2f}%<extra></extra>')
        ])
        fp_fig.update_layout(
            title="False Positive Rates by Filter",
            xaxis_title="Filter Type",
            yaxis_title="False Positive Rate (%)",
            template="plotly_white",
            margin=dict(l=40, r=40, t=40, b=40),
            showlegend=False
        )
        
        # Memory usage chart
        memory_fig = go.Figure(data=[
            go.Bar(x=filter_names, y=memory_usage,
                   marker_color=['#96CEB4', '#FFEAA7', '#DDA0DD'],
                   hovertemplate='<b>%{x}</b><br>Memory Usage: %{y:.1f} KB<extra></extra>')
        ])
        memory_fig.update_layout(
            title="Memory Usage by Filter",
            xaxis_title="Filter Type", 
            yaxis_title="Memory Usage (KB)",
            template="plotly_white",
            margin=dict(l=40, r=40, t=40, b=40),
            showlegend=False
        )
        
        return (cards, fp_fig, memory_fig, 
                str(total_filters), 
                f"{0.5:.1f}ms",  # Placeholder - could be calculated from performance data
                f"{avg_false_positive:.1%}", 
                f"{total_memory:.0f}KB")
        
    except requests.RequestException:
        error_card = dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.I(className="fas fa-exclamation-triangle text-warning fs-1 me-3"),
                    html.Div([
                        html.H4("⚠️ API Connection Error", className="text-warning mb-2"),
                        html.P("Cannot connect to bloom filter API.", className="mb-1"),
                        html.P("Please ensure the API server is running on port 8001.", className="mb-0")
                    ])
                ], className="d-flex align-items-center text-center")
            ])
        ], className="border-0 shadow-sm")
        
        empty_fig = go.Figure()
        empty_fig.update_layout(
            title="No Data Available", 
            template="plotly_white",
            annotations=[{
                'text': 'No data available',
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 20}
            }]
        )
        
        return ([error_card], empty_fig, empty_fig, "0", "0ms", "0%", "0KB")

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8002)

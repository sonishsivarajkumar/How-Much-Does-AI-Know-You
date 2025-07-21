"""Web server for AI Audit dashboard."""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import json
from pathlib import Path

from ..models import AuditReport, Inference, Platform
from ..storage import db
from ..config import settings

app = FastAPI(
    title="AI Audit Dashboard",
    description="Privacy audit web interface",
    version="0.1.0"
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await db.initialize()


@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the main dashboard."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Audit Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    </head>
    <body class="bg-gray-100">
        <div class="min-h-screen">
            <!-- Header -->
            <header class="bg-blue-600 text-white p-4">
                <div class="container mx-auto flex justify-between items-center">
                    <h1 class="text-2xl font-bold">🛡️ AI Audit Dashboard</h1>
                    <div class="space-x-4">
                        <button onclick="refreshData()" class="bg-blue-500 hover:bg-blue-700 px-4 py-2 rounded">
                            Refresh
                        </button>
                        <button onclick="runScan()" class="bg-green-500 hover:bg-green-700 px-4 py-2 rounded">
                            New Scan
                        </button>
                    </div>
                </div>
            </header>

            <!-- Main Content -->
            <main class="container mx-auto p-6">
                <!-- Status Cards -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <div class="bg-white p-6 rounded-lg shadow">
                        <h3 class="text-lg font-semibold text-gray-700">Privacy Risk</h3>
                        <p id="privacy-risk" class="text-3xl font-bold text-red-500">--</p>
                        <p class="text-sm text-gray-500">Out of 10</p>
                    </div>
                    <div class="bg-white p-6 rounded-lg shadow">
                        <h3 class="text-lg font-semibold text-gray-700">Inferences</h3>
                        <p id="inference-count" class="text-3xl font-bold text-blue-500">--</p>
                        <p class="text-sm text-gray-500">Total made</p>
                    </div>
                    <div class="bg-white p-6 rounded-lg shadow">
                        <h3 class="text-lg font-semibold text-gray-700">High Confidence</h3>
                        <p id="high-conf-count" class="text-3xl font-bold text-orange-500">--</p>
                        <p class="text-sm text-gray-500">Above 70%</p>
                    </div>
                    <div class="bg-white p-6 rounded-lg shadow">
                        <h3 class="text-lg font-semibold text-gray-700">Last Scan</h3>
                        <p id="last-scan" class="text-sm font-medium text-gray-700">--</p>
                        <p class="text-sm text-gray-500">Date & time</p>
                    </div>
                </div>

                <!-- Charts Section -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                    <!-- Confidence Distribution -->
                    <div class="bg-white p-6 rounded-lg shadow">
                        <h3 class="text-lg font-semibold text-gray-700 mb-4">Inference Confidence</h3>
                        <div id="confidence-chart" class="h-64"></div>
                    </div>
                    
                    <!-- Inference Types -->
                    <div class="bg-white p-6 rounded-lg shadow">
                        <h3 class="text-lg font-semibold text-gray-700 mb-4">Inference Types</h3>
                        <div id="types-chart" class="h-64"></div>
                    </div>
                </div>

                <!-- Inferences Table -->
                <div class="bg-white rounded-lg shadow">
                    <div class="p-6 border-b">
                        <h3 class="text-lg font-semibold text-gray-700">Recent Inferences</h3>
                    </div>
                    <div class="overflow-x-auto">
                        <table class="w-full">
                            <thead class="bg-gray-50">
                                <tr>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Value</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Confidence</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Source</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                                </tr>
                            </thead>
                            <tbody id="inferences-table" class="divide-y divide-gray-200">
                                <!-- Filled by JavaScript -->
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Recommendations -->
                <div class="mt-8 bg-white rounded-lg shadow">
                    <div class="p-6 border-b">
                        <h3 class="text-lg font-semibold text-gray-700">Privacy Recommendations</h3>
                    </div>
                    <div id="recommendations" class="p-6">
                        <!-- Filled by JavaScript -->
                    </div>
                </div>
            </main>
        </div>

        <script>
            let currentData = null;

            async function loadData() {
                try {
                    const response = await fetch('/api/dashboard-data');
                    currentData = await response.json();
                    updateDashboard();
                } catch (error) {
                    console.error('Failed to load data:', error);
                }
            }

            function updateDashboard() {
                if (!currentData) return;

                // Update status cards
                document.getElementById('privacy-risk').textContent = 
                    currentData.privacy_risk ? currentData.privacy_risk.toFixed(1) : '--';
                document.getElementById('inference-count').textContent = currentData.total_inferences || 0;
                document.getElementById('high-conf-count').textContent = currentData.high_confidence_count || 0;
                document.getElementById('last-scan').textContent = 
                    currentData.last_scan ? new Date(currentData.last_scan).toLocaleString() : 'Never';

                // Update charts
                updateConfidenceChart();
                updateTypesChart();

                // Update table
                updateInferencesTable();

                // Update recommendations
                updateRecommendations();
            }

            function updateConfidenceChart() {
                const data = [{
                    x: currentData.inferences?.map(i => i.confidence) || [],
                    type: 'histogram',
                    nbinsx: 10,
                    marker: { color: '#3B82F6' }
                }];

                const layout = {
                    title: '',
                    xaxis: { title: 'Confidence Score' },
                    yaxis: { title: 'Count' },
                    margin: { t: 20, b: 40, l: 40, r: 20 }
                };

                Plotly.newPlot('confidence-chart', data, layout, {displayModeBar: false});
            }

            function updateTypesChart() {
                const typeCounts = {};
                currentData.inferences?.forEach(i => {
                    const type = i.type.replace(/_/g, ' ');
                    typeCounts[type] = (typeCounts[type] || 0) + 1;
                });

                const data = [{
                    values: Object.values(typeCounts),
                    labels: Object.keys(typeCounts),
                    type: 'pie',
                    textinfo: 'percent',
                    hoverinfo: 'label+value+percent'
                }];

                const layout = {
                    title: '',
                    margin: { t: 20, b: 20, l: 20, r: 20 }
                };

                Plotly.newPlot('types-chart', data, layout, {displayModeBar: false});
            }

            function updateInferencesTable() {
                const tbody = document.getElementById('inferences-table');
                tbody.innerHTML = '';

                const recent = currentData.inferences?.slice(0, 10) || [];
                recent.forEach(inference => {
                    const row = tbody.insertRow();
                    
                    // Type
                    const typeCell = row.insertCell();
                    typeCell.textContent = inference.type.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase());
                    typeCell.className = 'px-6 py-4 text-sm text-gray-900';
                    
                    // Value
                    const valueCell = row.insertCell();
                    valueCell.textContent = inference.value.length > 50 ? 
                        inference.value.substring(0, 50) + '...' : inference.value;
                    valueCell.className = 'px-6 py-4 text-sm text-gray-700';
                    
                    // Confidence
                    const confCell = row.insertCell();
                    const confValue = Math.round(inference.confidence * 100);
                    confCell.innerHTML = `<span class="px-2 py-1 text-xs font-medium rounded-full ${
                        confValue >= 70 ? 'bg-red-100 text-red-800' :
                        confValue >= 40 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                    }">${confValue}%</span>`;
                    confCell.className = 'px-6 py-4 text-sm';
                    
                    // Source
                    const sourceCell = row.insertCell();
                    sourceCell.textContent = inference.source_platforms?.join(', ') || 'Unknown';
                    sourceCell.className = 'px-6 py-4 text-sm text-gray-500';
                    
                    // Date
                    const dateCell = row.insertCell();
                    dateCell.textContent = new Date(inference.created_at).toLocaleDateString();
                    dateCell.className = 'px-6 py-4 text-sm text-gray-500';
                });
            }

            function updateRecommendations() {
                const container = document.getElementById('recommendations');
                container.innerHTML = '';

                if (!currentData.recommendations?.length) {
                    container.innerHTML = '<p class="text-gray-500">No recommendations available. Run a scan to get privacy suggestions.</p>';
                    return;
                }

                currentData.recommendations.forEach((rec, index) => {
                    const div = document.createElement('div');
                    div.className = 'mb-4 p-4 border rounded-lg';
                    
                    const priorityColor = rec.priority === 'high' ? 'border-red-200 bg-red-50' :
                                         rec.priority === 'medium' ? 'border-yellow-200 bg-yellow-50' :
                                         'border-green-200 bg-green-50';
                    div.className += ' ' + priorityColor;
                    
                    div.innerHTML = `
                        <h4 class="font-semibold text-gray-800">${rec.title}</h4>
                        <p class="text-gray-600 mt-1">${rec.description}</p>
                        <div class="mt-2">
                            <span class="text-xs px-2 py-1 rounded-full ${
                                rec.priority === 'high' ? 'bg-red-200 text-red-800' :
                                rec.priority === 'medium' ? 'bg-yellow-200 text-yellow-800' :
                                'bg-green-200 text-green-800'
                            }">${rec.priority.toUpperCase()}</span>
                        </div>
                    `;
                    
                    container.appendChild(div);
                });
            }

            function refreshData() {
                loadData();
            }

            function runScan() {
                alert('Scan functionality would trigger a new privacy audit. Use CLI for now: ai-audit scan');
            }

            // Load data on page load
            document.addEventListener('DOMContentLoaded', loadData);
        </script>
    </body>
    </html>
    """


@app.get("/api/dashboard-data")
async def get_dashboard_data():
    """Get data for the dashboard."""
    try:
        # Get recent inferences
        inferences = await db.get_recent_inferences(limit=100)
        
        # Get audit history
        history = await db.get_audit_history(limit=1)
        
        # Calculate stats
        high_confidence_count = len([i for i in inferences if i.confidence >= 0.7])
        
        # Get latest privacy risk score
        privacy_risk = None
        last_scan = None
        if history:
            latest = history[0]
            privacy_risk = latest.get("privacy_risk_score")
            last_scan = latest.get("generated_at")
        
        # Convert inferences to dict format
        inferences_data = []
        for inference in inferences:
            inferences_data.append({
                "type": inference.type.value,
                "value": inference.value,
                "confidence": inference.confidence,
                "source_platforms": [p.value for p in inference.source_platforms],
                "created_at": inference.created_at.isoformat(),
                "reasoning": inference.reasoning
            })
        
        # Mock recommendations for now
        recommendations = [
            {
                "title": "Remove Location Information",
                "description": "Your location can be inferred from your profiles",
                "priority": "high"
            },
            {
                "title": "Vary Activity Patterns", 
                "description": "Your schedule is predictable from commit patterns",
                "priority": "medium"
            }
        ]
        
        return {
            "total_inferences": len(inferences),
            "high_confidence_count": high_confidence_count,
            "privacy_risk": privacy_risk,
            "last_scan": last_scan,
            "inferences": inferences_data,
            "recommendations": recommendations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/inferences")
async def get_inferences(limit: int = 50, min_confidence: float = 0.0):
    """Get recent inferences."""
    try:
        inferences = await db.get_recent_inferences(limit=limit, min_confidence=min_confidence)
        return [
            {
                "type": i.type.value,
                "value": i.value,
                "confidence": i.confidence,
                "source_platforms": [p.value for p in i.source_platforms],
                "created_at": i.created_at.isoformat(),
                "reasoning": i.reasoning
            }
            for i in inferences
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audit-history")
async def get_audit_history(limit: int = 10):
    """Get audit report history."""
    try:
        history = await db.get_audit_history(limit=limit)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def start_web_server(host: str = "127.0.0.1", port: int = 8000):
    """Start the web server."""
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info" if settings.debug_mode else "warning"
    )

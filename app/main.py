"""
ARK Enterprise Email Intelligence - Dashboard
The UI that sells for $200K/year contracts
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ARK Enterprise - Email Intelligence")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
def enterprise_dashboard():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
      <head>
        <title>ARK Enterprise Email Intelligence</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            body { 
                font-family: 'Inter', sans-serif;
                background: #0F172A;
                color: #E2E8F0;
                min-height: 100vh;
            }
            
            .header {
                background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
                padding: 24px 40px;
                border-bottom: 1px solid #334155;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .logo {
                font-size: 24px;
                font-weight: 800;
                background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .scan-btn {
                background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%);
                color: white;
                border: none;
                padding: 12px 32px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 15px;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
                transition: all 0.3s;
            }
            
            .scan-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(59, 130, 246, 0.6);
            }
            
            .scan-btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 40px;
            }
            
            .summary-card {
                background: linear-gradient(135deg, #1E40AF 0%, #7C3AED 100%);
                padding: 40px;
                border-radius: 16px;
                margin-bottom: 32px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.3);
            }
            
            .summary-title {
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 8px;
            }
            
            .summary-subtitle {
                font-size: 16px;
                opacity: 0.9;
                margin-bottom: 24px;
            }
            
            .summary-text {
                font-size: 14px;
                line-height: 1.8;
                white-space: pre-wrap;
                font-family: 'Courier New', monospace;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 32px;
            }
            
            .stat-card {
                background: #1E293B;
                padding: 24px;
                border-radius: 12px;
                border: 1px solid #334155;
                transition: all 0.3s;
            }
            
            .stat-card:hover {
                border-color: #3B82F6;
                transform: translateY(-4px);
                box-shadow: 0 8px 24px rgba(59, 130, 246, 0.2);
            }
            
            .stat-icon {
                font-size: 32px;
                margin-bottom: 12px;
            }
            
            .stat-value {
                font-size: 36px;
                font-weight: 700;
                margin-bottom: 8px;
            }
            
            .stat-label {
                font-size: 14px;
                color: #94A3B8;
                font-weight: 500;
            }
            
            .section-title {
                font-size: 20px;
                font-weight: 700;
                margin-bottom: 20px;
                color: #F1F5F9;
            }
            
            .email-list {
                background: #1E293B;
                border-radius: 12px;
                border: 1px solid #334155;
                overflow: hidden;
            }
            
            .email-item {
                padding: 16px 20px;
                border-bottom: 1px solid #334155;
                display: grid;
                grid-template-columns: 40px 1fr 150px 120px 120px;
                gap: 16px;
                align-items: center;
                transition: background 0.2s;
            }
            
            .email-item:hover {
                background: #334155;
            }
            
            .email-item:last-child {
                border-bottom: none;
            }
            
            .category-badge {
                padding: 4px 12px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                text-align: center;
            }
            
            .team-badge {
                padding: 4px 12px;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                background: #334155;
                color: #94A3B8;
                text-align: center;
            }
            
            .priority-badge {
                padding: 4px 12px;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 700;
                text-align: center;
            }
            
            .priority-high { background: #DC2626; color: white; }
            .priority-medium { background: #F59E0B; color: white; }
            .priority-low { background: #10B981; color: white; }
            
            .loading {
                text-align: center;
                padding: 60px;
                font-size: 18px;
            }
            
            .spinner {
                border: 4px solid #334155;
                border-top: 4px solid #3B82F6;
                border-radius: 50%;
                width: 48px;
                height: 48px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .chart-container {
                background: #1E293B;
                padding: 24px;
                border-radius: 12px;
                border: 1px solid #334155;
                margin-bottom: 32px;
            }
        </style>
      </head>
      <body>
        <div class="header">
            <div class="logo">ARK Enterprise 🚀</div>
            <button class="scan-btn" onclick="scanInbox()" id="scanBtn">Scan Inbox (200-300 emails)</button>
        </div>
        
        <div class="container">
            <div id="loading" class="loading" style="display:none;">
                <div class="spinner"></div>
                <p>Processing emails... This may take 30-60 seconds</p>
            </div>
            
            <div id="results" style="display:none;">
                <!-- Daily Summary Card -->
                <div class="summary-card">
                    <div class="summary-title">📊 Daily Email Intelligence</div>
                    <div class="summary-subtitle" id="summarySubtitle"></div>
                    <div class="summary-text" id="summaryText"></div>
                </div>
                
                <!-- Stats Grid -->
                <div class="stats-grid" id="statsGrid"></div>
                
                <!-- Charts -->
                <div class="chart-container">
                    <h3 class="section-title">Category Distribution</h3>
                    <canvas id="categoryChart" width="400" height="100"></canvas>
                </div>
                
                <!-- Email List -->
                <h3 class="section-title">Processed Emails</h3>
                <div class="email-list" id="emailList"></div>
            </div>
        </div>
        
        <script>
          async function scanInbox() {
            const btn = document.getElementById('scanBtn');
            const loading = document.getElementById('loading');
            const results = document.getElementById('results');
            
            btn.disabled = true;
            btn.textContent = 'Scanning...';
            loading.style.display = 'block';
            results.style.display = 'none';
            
            try {
                const response = await fetch('http://localhost:8000/api/v1/batch/scan', {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (data.ok) {
                    displayResults(data.results);
                } else {
                    alert('Error: ' + (data.error || 'Unknown error'));
                }
            } catch (e) {
                alert('Network error: ' + e.message);
            } finally {
                btn.disabled = false;
                btn.textContent = 'Scan Inbox (200-300 emails)';
                loading.style.display = 'none';
            }
          }
          
          function displayResults(data) {
            const results = document.getElementById('results');
            results.style.display = 'block';
            
            // Summary
            document.getElementById('summarySubtitle').textContent = 
                `Processed ${data.stats.total} emails in ${data.elapsed_seconds.toFixed(1)}s`;
            document.getElementById('summaryText').textContent = data.summary;
            
            // Stats Grid
            const statsGrid = document.getElementById('statsGrid');
            statsGrid.innerHTML = `
                <div class="stat-card">
                    <div class="stat-icon">📧</div>
                    <div class="stat-value">${data.stats.total}</div>
                    <div class="stat-label">Total Emails</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">✅</div>
                    <div class="stat-value">${data.stats.auto_replied}</div>
                    <div class="stat-label">Auto-Replied</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">📅</div>
                    <div class="stat-value">${data.stats.meetings_scheduled}</div>
                    <div class="stat-label">Meetings Scheduled</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">🎫</div>
                    <div class="stat-value">${data.stats.tickets_created}</div>
                    <div class="stat-label">Tickets Created</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">⚠️</div>
                    <div class="stat-value">${data.stats.escalations}</div>
                    <div class="stat-label">Escalated to CEO</div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">⏱️</div>
                    <div class="stat-value">${data.performance.emails_per_second.toFixed(1)}</div>
                    <div class="stat-label">Emails/Second</div>
                </div>
            `;
            
            // Email List
            const emailList = document.getElementById('emailList');
            emailList.innerHTML = data.results.slice(0, 50).map(email => `
                <div class="email-item">
                    <span class="stat-icon" style="font-size:24px;">${getCategoryIcon(email.category)}</span>
                    <div>
                        <div style="font-weight:600; margin-bottom:4px;">${email.subject}</div>
                        <div style="font-size:13px; color:#94A3B8;">${email.from}</div>
                    </div>
                    <span class="category-badge" style="background:${getCategoryColor(email.category)};">
                        ${email.category.replace('_', ' ').toUpperCase()}
                    </span>
                    <span class="team-badge">${email.team.replace('_', ' ')}</span>
                    <span class="priority-badge priority-${getPriorityClass(email.priority)}">
                        P${email.priority}
                    </span>
                </div>
            `).join('');
            
            // Draw Chart
            drawCategoryChart(data.stats);
          }
          
          function getCategoryIcon(category) {
            const icons = {
                meetings: '📅', complaints: '🚨', client_requests: '💬',
                hr_issues: '👥', finance: '💰', it_support: '🔧',
                sales: '📈', project_updates: '📋', invoices: '🧾',
                escalations: '⚠️', followup: '⏰', internal: '📊',
                unknown: '❓'
            };
            return icons[category] || '📧';
          }
          
          function getCategoryColor(category) {
            const colors = {
                meetings: '#4CAF50', complaints: '#F44336', client_requests: '#2196F3',
                hr_issues: '#FF9800', finance: '#4CAF50', it_support: '#607D8B',
                sales: '#8BC34A', project_updates: '#00BCD4', invoices: '#FFC107',
                escalations: '#E91E63', followup: '#03A9F4', internal: '#9C27B0',
                unknown: '#9E9E9E'
            };
            return colors[category] || '#9E9E9E';
          }
          
          function getPriorityClass(priority) {
            if (priority >= 8) return 'high';
            if (priority >= 5) return 'medium';
            return 'low';
          }
          
          function drawCategoryChart(stats) {
            const ctx = document.getElementById('categoryChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: Object.keys(stats).filter(k => !['total', 'processed', 'auto_replied', 'escalated', 'meetings_scheduled', 'tickets_created', 'archived'].includes(k)),
                    datasets: [{
                        label: 'Email Count',
                        data: Object.keys(stats).filter(k => !['total', 'processed', 'auto_replied', 'escalated', 'meetings_scheduled', 'tickets_created', 'archived'].includes(k)).map(k => stats[k]),
                        backgroundColor: 'rgba(59, 130, 246, 0.8)',
                        borderColor: 'rgba(59, 130, 246, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: { beginAtZero: true, ticks: { color: '#94A3B8' }, grid: { color: '#334155' } },
                        x: { ticks: { color: '#94A3B8' }, grid: { display: false } }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
          }
        </script>
      </body>
    </html>
    """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

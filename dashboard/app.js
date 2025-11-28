const API_URL = 'http://localhost:8000/api/v1/batch';

// Initialize Charts
let volumeChart, intentChart;

document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    refreshData();
});

function initCharts() {
    // Volume Chart
    const ctxVolume = document.getElementById('volumeChart').getContext('2d');
    volumeChart = new Chart(ctxVolume, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Emails Processed',
                data: [65, 59, 80, 81, 56, 55, 40],
                borderColor: '#3B82F6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { grid: { color: '#1F2937' }, ticks: { color: '#94A3B8' } },
                x: { grid: { display: false }, ticks: { color: '#94A3B8' } }
            }
        }
    });

    // Intent Chart
    const ctxIntent = document.getElementById('intentChart').getContext('2d');
    intentChart = new Chart(ctxIntent, {
        type: 'doughnut',
        data: {
            labels: ['Support', 'Sales', 'Finance', 'Other'],
            datasets: [{
                data: [30, 20, 15, 35],
                backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#64748B'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'bottom', labels: { color: '#94A3B8' } }
            },
            cutout: '70%'
        }
    });
}

async function refreshData() {
    try {
        // Fetch Status
        const statusRes = await fetch(`${API_URL}/status`);
        const statusData = await statusRes.json();

        // Fetch Results
        const resultsRes = await fetch(`${API_URL}/results`);
        const resultsData = await resultsRes.json();

        if (resultsData.ok && resultsData.results) {
            updateStats(resultsData.results);
            updateTable(resultsData.results);
            updateCharts(resultsData.results);
        } else {
            console.log('No results found');
        }

    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

function updateStats(results) {
    const total = results.length;
    const urgent = results.filter(r => r.urgency === 'high' || r.urgency === 'critical').length;
    const resolved = Math.floor(total * 0.4); // Mock data for resolved

    document.getElementById('totalEmails').textContent = total;
    document.getElementById('urgentCount').textContent = urgent;
    document.getElementById('resolvedCount').textContent = resolved;
}

function updateTable(results) {
    const tbody = document.getElementById('activityTable');
    tbody.innerHTML = '';

    // Show last 5 results
    const recent = results.slice(0, 5);

    recent.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="color: #94A3B8;">${r.id || 'N/A'}</td>
            <td>${formatIntent(r.intent)}</td>
            <td><span class="badge ${r.urgency}">${r.urgency}</span></td>
            <td>${Math.round(r.confidence * 100)}%</td>
            <td><span class="badge processed">Auto-Routed</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function updateCharts(results) {
    // Update Intent Chart
    const intents = {};
    results.forEach(r => {
        const key = r.intent || 'other';
        intents[key] = (intents[key] || 0) + 1;
    });

    const labels = Object.keys(intents).map(formatIntent);
    const data = Object.values(intents);

    intentChart.data.labels = labels;
    intentChart.data.datasets[0].data = data;
    intentChart.update();
}

function formatIntent(intent) {
    if (!intent) return 'Unknown';
    return intent.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
}

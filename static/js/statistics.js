let statusChart, clientsChart, monthlyChart, responseRateChart, popularHoursChart;

function loadStatistics() {
    fetch('/admin/statistics/data')
        .then(response => response.json())
        .then(data => {
            renderKPIs(data);
            renderStatusChart(data);
            renderClientsChart(data);
            renderMonthlyChart(data);
            renderResponseRateChart(data);
            renderPopularHoursChart(data);
        })
        .catch(err => {
            console.error('Error loading statistics:', err);
            alert('Failed to load statistics data');
        });
}

function renderKPIs(data) {
    const html = `
        <div class="kpi-card">
            <h4>Total Bookings</h4>
            <div class="kpi-value">${data.total_bookings}</div>
        </div>
        <div class="kpi-card">
            <h4>Confirmed</h4>
            <div class="kpi-value" style="color:#10b981;">${data.confirmed}</div>
        </div>
        <div class="kpi-card">
            <h4>Pending</h4>
            <div class="kpi-value" style="color:#f59e0b;">${data.pending}</div>
        </div>
        <div class="kpi-card">
            <h4>Cancelled</h4>
            <div class="kpi-value" style="color:#ef4444;">${data.cancelled}</div>
        </div>
        <div class="kpi-card">
            <h4>Response Rate</h4>
            <div class="kpi-value">${data.response_rate}%</div>
            <div class="kpi-sub">Average client response</div>
        </div>
    `;
    document.getElementById('kpi-grid').innerHTML = html;
}

function renderStatusChart(data) {
    if (statusChart) statusChart.destroy();
    statusChart = new Chart(document.getElementById('statusChart'), {
        type: 'doughnut',
        data: {
            labels: ['Confirmed', 'Pending', 'Cancelled', 'Tentative'],
            datasets: [{
                data: [data.confirmed, data.pending, data.cancelled, data.tentative],
                backgroundColor: ['#10b981', '#f59e0b', '#ef4444', '#6366f1'],
                borderColor: '#0f0f1a',
                borderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { color: '#e0e0ff', padding: 20 }}
            }
        }
    });
}

function renderClientsChart(data) {
    if (clientsChart) clientsChart.destroy();
    const names = data.clients.map(c => c.name);
    const totals = data.clients.map(c => c.total);

    clientsChart = new Chart(document.getElementById('clientsChart'), {
        type: 'bar',
        data: {
            labels: names,
            datasets: [{ label: 'Total Bookings', data: totals, backgroundColor: '#7c3aed', borderRadius: 6 }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { color: '#1f1f2e' }, ticks: { color: '#94a3b8' }},
                y: { grid: { color: '#1f1f2e' }, ticks: { color: '#e0e0ff' }}
            }
        }
    });
}

function renderMonthlyChart(data) {
    if (monthlyChart) monthlyChart.destroy();
    const months = data.bookings_per_month.map(m => m.month);
    const counts = data.bookings_per_month.map(m => m.count);

    monthlyChart = new Chart(document.getElementById('monthlyChart'), {
        type: 'line',
        data: {
            labels: months,
            datasets: [{
                label: 'Bookings',
                data: counts,
                borderColor: '#7c3aed',
                backgroundColor: 'rgba(124, 58, 237, 0.1)',
                tension: 0.4,
                borderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { color: '#1f1f2e' }, ticks: { color: '#94a3b8' }},
                y: { grid: { color: '#1f1f2e' }, ticks: { color: '#94a3b8' }}
            }
        }
    });
}

function renderResponseRateChart(data) {
    if (responseRateChart) responseRateChart.destroy();
    const names = data.clients.map(c => c.name);
    const rates = data.clients.map(c => Math.round((c.confirmed / c.total) * 100));

    responseRateChart = new Chart(document.getElementById('responseRateChart'), {
        type: 'bar',
        data: {
            labels: names,
            datasets: [{ label: 'Response Rate %', data: rates, backgroundColor: '#10b981', borderRadius: 6 }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { min: 0, max: 100, ticks: { callback: v => v + '%', color: '#94a3b8' }},
                x: { grid: { color: '#1f1f2e' }, ticks: { color: '#e0e0ff' }}
            }
        }
    });
}

function renderPopularHoursChart(data) {
    if (popularHoursChart) popularHoursChart.destroy();
    const hours = data.popular_hours.map(h => h.hour);
    const counts = data.popular_hours.map(h => h.count);

    popularHoursChart = new Chart(document.getElementById('popularHoursChart'), {
        type: 'bar',
        data: {
            labels: hours,
            datasets: [{ label: 'Bookings', data: counts, backgroundColor: '#6366f1', borderRadius: 6 }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { grid: { color: '#1f1f2e' }, ticks: { color: '#94a3b8' }},
                x: { grid: { color: '#1f1f2e' }, ticks: { color: '#e0e0ff' }}
            }
        }
    });
}

// Auto load when page is ready
document.addEventListener('DOMContentLoaded', loadStatistics);
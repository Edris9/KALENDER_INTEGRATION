let selectedSlot = null;
let selectedClient = null;
let currentYear = new Date().getFullYear();
let currentMonth = new Date().getMonth();
let freeSlotsData = {};

function loadClients() {
    fetch('/admin/clients')
        .then(r => r.json())
        .then(data => {
            const list = document.getElementById('clients-list');
            if (data.clients.length === 0) {
                list.innerHTML = '<div class="empty">No clients connected yet.</div>';
                return;
            }
            list.innerHTML = '';
            data.clients.forEach(client => {
                const card = document.createElement('div');
                card.className = 'client-card';
                card.id = `client-card-${client.id}`;
                card.innerHTML = `
                    <div class="client-info">
                        <h3>${client.name}</h3>
                        <p>${client.email}</p>
                    </div>
                    <div class="client-card-footer">
                        <span class="status connected">Connected</span>
                        <button class="view-btn" onclick="selectClient('${client.id}', '${client.name}')">View Calendar</button>
                    </div>
                `;
                list.appendChild(card);
            });
        });
}

function selectClient(clientId, clientName) {
    selectedClient = clientId;
    document.querySelectorAll('.client-card').forEach(c => c.classList.remove('selected'));
    const activeCard = document.getElementById(`client-card-${clientId}`);
    if (activeCard) activeCard.classList.add('selected');
    document.getElementById('placeholder').style.display = 'none';
    document.getElementById('client-details-tabs').style.display = 'block';
    document.getElementById('selected-client-name').innerText = clientName;
    switchTab('calendar');
    loadCalendar(clientId);
}

function loadCalendar(clientId) {
    const calWrap = document.getElementById('cal-wrap');
    calWrap.innerHTML = '<div class="empty">Loading...</div>';
    document.getElementById('admin-booking-form').style.display = 'none';
    document.getElementById('admin-confirmation').style.display = 'none';

    fetch(`/admin/availability/${clientId}`)
        .then(r => r.json())
        .then(data => {
            freeSlotsData = {};
            if (data.Free_slots) {
                data.Free_slots.forEach(slot => {
                    const date = slot.Start.split(' ')[0];
                    if (!freeSlotsData[date]) freeSlotsData[date] = [];
                    freeSlotsData[date].push(slot);
                });
            }
            renderCalendar();
        });
}

function loadUnreadCount() {
    fetch('/admin/unread-bookings')
        .then(r => r.json())
        .then(data => {
            const badge = document.getElementById('history-badge');
            if (data.count > 0) {
                badge.textContent = data.count;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        });
}

function renderCalendar() {
    const calWrap = document.getElementById('cal-wrap');
    const today = new Date();
    const todayStr = today.toISOString().split('T')[0];
    const monthLabel = new Date(currentYear, currentMonth, 1)
        .toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
    const firstDay = new Date(currentYear, currentMonth, 1).getDay();
    const offset = firstDay === 0 ? 6 : firstDay - 1;
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();

    let daysHTML = '';
    for (let i = 0; i < offset; i++) {
        daysHTML += '<div class="cal-day empty"></div>';
    }
    for (let d = 1; d <= daysInMonth; d++) {
        const date = new Date(currentYear, currentMonth, d);
        const dow = date.getDay();
        const isWeekend = dow === 0 || dow === 6;
        const key = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
        const isToday = key === todayStr;
        const hasSlots = freeSlotsData[key] && freeSlotsData[key].length > 0;
        let cls = 'cal-day';
        if (isWeekend) cls += ' weekend';
        else if (isToday) cls += ' today';
        if (hasSlots) cls += ' has-slots';
        const click = `onclick="showSlots('${key}')"`;
        daysHTML += `<div class="${cls}" ${click}>${d}</div>`;
    }

    calWrap.innerHTML = `
        <div class="cal-layout">
            <div class="cal-grid-wrap">
                <div class="cal-header">
                    <button onclick="changeMonth(-1)">&#8249;</button>
                    <span>${monthLabel}</span>
                    <button onclick="changeMonth(1)">&#8250;</button>
                </div>
                <div class="cal-days-header">
                    <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span>
                    <span class="wknd">Sat</span><span class="wknd">Sun</span>
                </div>
                <div class="cal-days" id="cal-days">${daysHTML}</div>
            </div>
            <div class="slots-panel">
                <h4 id="slots-label">Select a day</h4>
                <div id="slots-list"><div class="no-slots">Click a day to see available times</div></div>
            </div>
        </div>
    `;
}

function showSlots(key) {
    document.querySelectorAll('.cal-day').forEach(d => d.classList.remove('selected-day'));
    document.querySelectorAll('.cal-day:not(.empty)').forEach(d => {
        const dayNum = parseInt(key.split('-')[2]);
        if (parseInt(d.textContent) === dayNum) d.classList.add('selected-day');
    });

    const date = new Date(key + 'T12:00:00');
    const label = date.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });
    document.getElementById('slots-label').textContent = label;

    const list = document.getElementById('slots-list');
    const slots = freeSlotsData[key];
    if (!slots || slots.length === 0) {
        list.innerHTML = '<div class="no-slots">No available slots</div>';
        return;
    }
    list.innerHTML = '';
    slots.forEach(slot => {
        const el = document.createElement('div');
        el.className = 'slot-item';
        el.textContent = `${slot.Start.split(' ')[1]} – ${slot.End.split(' ')[1]}`;
        el.onclick = () => selectSlot(el, slot);
        list.appendChild(el);
    });

    document.getElementById('admin-booking-form').style.display = 'none';
    document.getElementById('admin-confirmation').style.display = 'none';
    selectedSlot = null;
}

function selectSlot(el, slot) {
    document.querySelectorAll('.slot-item').forEach(s => s.classList.remove('selected-slot'));
    el.classList.add('selected-slot');
    selectedSlot = slot;
    document.getElementById('admin-selected-info').innerText =
        `Selected: ${slot.Start} – ${slot.End.split(' ')[1]}`;
    document.getElementById('admin-booking-form').style.display = 'block';
    document.getElementById('admin-booking-form').scrollIntoView({ behavior: 'smooth' });
}

function changeMonth(dir) {
    currentMonth += dir;
    if (currentMonth > 11) { currentMonth = 0; currentYear++; }
    if (currentMonth < 0) { currentMonth = 11; currentYear--; }
    renderCalendar();
    document.getElementById('admin-booking-form').style.display = 'none';
    selectedSlot = null;
}

function adminBookMeeting() {
    const name = document.getElementById('lead-name').value.trim();
    const email = document.getElementById('lead-email').value.trim();
    if (!name || !email || !selectedSlot || !selectedClient) {
        alert('Please fill in all fields!');
        return;
    }
    const btn = document.querySelector('#admin-booking-form .book-btn');
    btn.innerText = 'Booking...';
    btn.disabled = true;

    fetch(`/admin/book/${selectedClient}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            title: `Meeting with ${name}`,
            start_tid: selectedSlot.Start.replace(' ', 'T') + ':00+01:00',
            slut_tid: selectedSlot.End.replace(' ', 'T') + ':00+01:00',
            email: email
        })
    })
    .then(r => r.json())
    .then(data => {
        document.getElementById('admin-booking-form').style.display = 'none';
        const confirmation = document.getElementById('admin-confirmation');
        confirmation.innerHTML = `
            <div class="icon">🎉</div>
            <h2>Meeting Booked!</h2>
            <p>📅 <strong>${selectedSlot.Start} – ${selectedSlot.End.split(' ')[1]}</strong></p>
            <p>👤 <strong>${name}</strong> (${email})</p>
            <p>📧 Calendar invite sent to both parties.</p>
            ${data.Calendar_link ? `<a href="${data.Calendar_link}" target="_blank" style="color:#4285f4;">View in Calendar →</a>` : ''}
            <br><br>
            <button class="book-btn" onclick="location.reload()">Book Another</button>
        `;
        confirmation.style.display = 'block';
        confirmation.scrollIntoView({ behavior: 'smooth' });
    })
    .catch(() => {
        btn.innerText = 'Confirm Booking';
        btn.disabled = false;
        alert('Something went wrong!');
    });
}

function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.style.display = 'none';
    });
    const activeTab = document.getElementById(`tab-${tabName}`);
    if (activeTab) activeTab.style.display = 'block';
}

function loadHistory() {
    fetch(`/admin/bookings?client_id=${selectedClient}`)
        .then(r => r.json())
        .then(data => {
            const container = document.getElementById('tab-history');
            if (data.bookings.length === 0) {
                container.innerHTML = '<div class="section"><div class="coming-soon">No bookings yet</div></div>';
                return;
            }
            let html = '<div class="section"><table class="bookings-table"><thead><tr><th>Lead</th><th>Email</th><th>Meeting</th><th>Time</th><th>Status</th><th>Link</th></tr></thead><tbody>';
            data.bookings.forEach(b => {
                html += `<tr>
                    <td>${b.lead_name}</td>
                    <td>${b.lead_email}</td>
                    <td>${b.meeting_title}</td>
                    <td>${b.start_time.replace('T', ' ').slice(0, 16)}</td>
                    <td><span class="status-badge ${b.status}">${b.status}</span></td>
                    <td>${b.calendar_link ? `<a href="${b.calendar_link}" target="_blank">View</a>` : '-'}</td>
                </tr>`;
            });
            html += '</tbody></table></div>';
            container.innerHTML = html;

            // Markera som lästa
            fetch('/admin/bookings/mark-read', { method: 'POST' });
            document.getElementById('history-badge').style.display = 'none';
        });
}
    
document.addEventListener('DOMContentLoaded', () => {
    loadClients();
    loadUnreadCount();
    
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            switchTab(btn.dataset.tab);
            if (btn.dataset.tab === 'history') loadHistory();
        });
    });

    // Auto-refresh var 10:e sekund
    setInterval(() => {
        const historyTab = document.getElementById('tab-history');
        if (historyTab && historyTab.style.display !== 'none') {
            loadHistory();
        }
        loadUnreadCount();
    }, 10000);
});
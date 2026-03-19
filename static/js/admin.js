let selectedSlot = null;
let selectedClient = null;

// Hämta klienter från databasen
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
                card.innerHTML = `
                    <div class="client-info">
                        <h3>${client.name}</h3>
                        <p>${client.email}</p>
                    </div>
                    <div style="display:flex; gap:10px; align-items:center;">
                        <span class="status connected">Connected</span>
                        <button class="view-btn" onclick="selectClient('${client.id}', '${client.name}')">View Calendar</button>
                    </div>
                `;
                list.appendChild(card);
            });
        });
}

// Välj klient och visa deras kalender
function selectClient(clientId, clientName) {
    selectedClient = clientId;
    document.getElementById('selected-client-name').innerText = clientName;
    document.getElementById('calendar-section').style.display = 'block';
    document.getElementById('calendar-section').scrollIntoView({behavior: 'smooth'});

    fetch(`/admin/availability/${clientId}`)
        .then(r => r.json())
        .then(data => {
            const calendar = document.getElementById('admin-calendar');
            calendar.innerHTML = '';

            if (!data.Free_slots || data.Free_slots.length === 0) {
                calendar.innerHTML = '<div class="empty">No available slots.</div>';
                return;
            }

            // Gruppera per datum
            const byDate = {};
            data.Free_slots.forEach(slot => {
                const date = slot.Start.split(' ')[0];
                if (!byDate[date]) byDate[date] = [];
                byDate[date].push(slot);
            });

            Object.keys(byDate).forEach(date => {
                const dateLabel = document.createElement('div');
                dateLabel.style.cssText = 'font-size:13px; font-weight:600; color:#4285f4; margin:16px 0 8px;';
                dateLabel.innerText = new Date(date).toLocaleDateString('en-US', {weekday:'long', month:'long', day:'numeric'});
                calendar.appendChild(dateLabel);

                byDate[date].forEach(slot => {
                    const div = document.createElement('div');
                    div.className = 'slot';
                    div.innerText = `${slot.Start.split(' ')[1]} – ${slot.End.split(' ')[1]}`;
                    div.onclick = () => selectSlot(div, slot);
                    calendar.appendChild(div);
                });
            });
        });
}

// Välj tid
function selectSlot(el, slot) {
    document.querySelectorAll('.slot').forEach(s => s.classList.remove('selected'));
    el.classList.add('selected');
    selectedSlot = slot;

    document.getElementById('admin-booking-form').style.display = 'block';
    document.getElementById('admin-selected-info').innerText = 
        `Selected: ${slot.Start} – ${slot.End.split(' ')[1]}`;
    document.getElementById('admin-booking-form').scrollIntoView({behavior: 'smooth'});
}

// Boka möte
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
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            title: `Meeting with ${name}`,
            start_tid: selectedSlot.Start.replace(' ', 'T') + ':00+01:00',
            slut_tid: selectedSlot.End.replace(' ', 'T') + ':00+01:00',
            email: email
        })
    })
    .then(r => r.json())
    .then(data => {
        document.getElementById('calendar-section').style.display = 'none';
        document.getElementById('admin-booking-form').style.display = 'none';

        // Feature 1 — App status update med detaljer
        const confirmation = document.getElementById('admin-confirmation');
        confirmation.innerHTML = `
            <div class="icon">🎉</div>
            <h2>Meeting Booked!</h2>
            <p>📅 <strong>${selectedSlot.Start} – ${selectedSlot.End.split(' ')[1]}</strong></p>
            <p>👤 <strong>${name}</strong> (${email})</p>
            <p>📧 Calendar invite sent to both parties.</p>
            ${data.Calendar_link ? `<a href="${data.Calendar_link}" target="_blank" style="color:#4285f4;">View in Google Calendar →</a>` : ''}
            <br><br>
            <button class="book-btn" onclick="location.reload()">Book Another</button>
        `;
        confirmation.style.display = 'block';
        confirmation.scrollIntoView({behavior: 'smooth'});
    })
    .catch(() => {
        btn.innerText = 'Confirm Booking';
        btn.disabled = false;
        alert('Something went wrong!');
    });
}

// Ladda klienter när sidan öppnas
document.addEventListener('DOMContentLoaded', loadClients);
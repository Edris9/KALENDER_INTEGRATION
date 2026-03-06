let selectedSlot = null;
let currentMonday = new Date();
currentMonday.setDate(currentMonday.getDate() - currentMonday.getDay() + 1);

function renderWeek() {
  const grid = document.getElementById('calendar-grid');
  grid.innerHTML = '';

  const title = document.getElementById('week-title');
  const mon = new Date(currentMonday);
  title.textContent = `Week ${getWeekNumber(mon)}, ${mon.getFullYear()}`;

  for (let i = 0; i < 7; i++) {
    const day = new Date(currentMonday);
    day.setDate(day.getDate() + i);

    const col = document.createElement('div');
    col.className = 'day-column';
    if (isToday(day)) col.classList.add('today');

    const header = document.createElement('div');
    header.className = 'day-header';
    header.innerHTML = `
      <div class="weekday">${day.toLocaleDateString('en-US', {weekday:'short'})}</div>
      <div class="date">${day.getDate()}</div>
    `;
    col.appendChild(header);

    const slotsContainer = document.createElement('div');
    slotsContainer.id = `slots-${day.toISOString().split('T')[0]}`;
    col.appendChild(slotsContainer);

    grid.appendChild(col);
  }

  fetchAvailabilityForWeek();
}

function isToday(d) {
  const today = new Date();
  return d.toDateString() === today.toDateString();
}

function getWeekNumber(d) {
  d = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
  d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay()||7));
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(),0,1));
  return Math.ceil((((d - yearStart) / 86400000) + 1)/7);
}

function changeWeek(delta) {
  currentMonday.setDate(currentMonday.getDate() + delta * 7);
  renderWeek();
}

function fetchAvailabilityForWeek() {
  fetch('/availability')
    .then(r => r.json())
    .then(data => {
      if (!data.Free_slots) return;

      const byDate = {};
      (data.Free_slots || []).forEach(slot => {
        const dateKey = slot.Start.split(' ')[0];
        if (!byDate[dateKey]) byDate[dateKey] = [];
        byDate[dateKey].push(slot);
      });

      Object.keys(byDate).forEach(dateKey => {
        const container = document.getElementById(`slots-${dateKey}`);
        if (!container) return;

        byDate[dateKey].forEach(slot => {
          const div = document.createElement('div');
          const startTime = slot.Start.split(' ')[1]?.slice(0,5) || '';
          const endTime   = slot.End.split(' ')[1]?.slice(0,5) || '';

          div.className = 'slot available';
          div.innerHTML = `
            <div class="time">${startTime}</div>
            <div class="status">${startTime} – ${endTime}</div>
          `;
          div.onclick = () => selectSlot(div, slot);
          container.appendChild(div);
        });
      });
    })
    .catch(err => console.error('Fetch error:', err));
}

function selectSlot(el, slot) {
  document.querySelectorAll('.slot.available').forEach(s => s.classList.remove('selected'));
  el.classList.add('selected');
  selectedSlot = slot;

  document.getElementById('selected-info').innerText =
    `Selected: ${slot.Start} – ${slot.End.split(' ')[1] || ''}`;

  document.getElementById('booking-form').style.display = 'block';
  document.getElementById('booking-form').scrollIntoView({behavior:'smooth'});
}

function bookMeeting() {
  const name  = document.getElementById('name').value.trim();
  const email = document.getElementById('email').value.trim();

  if (!name || !email || !selectedSlot) {
    alert('Please fill in name and email!');
    return;
  }

  const start = selectedSlot.Start.replace(' ', 'T') + ':00+01:00';
  const end   = selectedSlot.End.replace(' ', 'T') + ':00+01:00';

  fetch('/book', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      title: `Meeting with ${name}`,
      start_tid: start,
      slut_tid: end,
      email: email
    })
  })
  .then(r => r.json())
  .then(() => {
    document.getElementById('calendar-grid').style.display = 'none';
    document.getElementById('booking-form').style.display = 'none';
    document.getElementById('confirmation').style.display = 'block';
  })
  .catch(() => alert('Something went wrong during booking.'));
}

// Init
document.addEventListener('DOMContentLoaded', () => {
  fetch('/availability')
    .then(r => r.json())
    .then(data => {
      if (data.Free_slots !== undefined) {
        document.getElementById('login-section').style.display = 'none';
        document.getElementById('main-content').style.display = 'block';
        renderWeek();
      }
    })
    .catch(() => {});
});
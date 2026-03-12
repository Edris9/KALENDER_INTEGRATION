import base64

with open('email_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

with open('theshowcaseai_logo.jpg', 'rb') as f:
    logo_b64 = base64.b64encode(f.read()).decode()

with open('imag.png', 'rb') as f:
    brain_b64 = base64.b64encode(f.read()).decode()

html = html.replace('{{LOGO_URL}}', f'data:image/jpeg;base64,{logo_b64}')
html = html.replace('{{BRAIN_URL}}', f'data:image/png;base64,{brain_b64}')
html = html.replace('{{LEAD_NAME}}', 'John Doe')
html = html.replace('{{LEAD_EMAIL}}', 'john@example.com')
html = html.replace('{{MEETING_TITLE}}', 'Meeting with John Doe')
html = html.replace('{{DATE}}', 'Thursday 12 March 2026')
html = html.replace('{{TIME_START}}', '10:00')
html = html.replace('{{TIME_END}}', '11:00')
html = html.replace('{{CALENDAR_LINK}}', '#')

with open('preview.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('preview.html')
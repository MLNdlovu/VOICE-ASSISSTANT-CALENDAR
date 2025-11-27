#!/usr/bin/env python3
"""Add voice assistant UI to dashboard.html"""

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find insertion point
insert_pos = content.find('</body>')
if insert_pos == -1:
    print("ERROR: Could not find </body> tag")
else:
    voice_ui = '''
<!-- Voice Assistant UI -->
<div id="triggerSetting" style="position:fixed;left:20px;bottom:20px;z-index:9998;background:rgba(0,0,0,0.8);padding:12px;border-radius:8px;border:1px solid #7C3AED">
    <div style="color:#fff;font-size:12px;margin-bottom:8px;font-weight:500">Voice Trigger</div>
    <input id="triggerInput" placeholder="Set trigger e.g. 'hey nova'" style="width:180px;padding:6px;border-radius:4px;border:none;background:rgba(255,255,255,0.1);color:#fff;margin-bottom:8px;display:block" autocomplete="off">
    <button id="saveTrigger" style="width:100%;padding:8px;background:#7C3AED;color:#fff;border:none;border-radius:4px;cursor:pointer;font-weight:500;font-size:11px;">Save (Hidden)</button>
</div>

<!-- Voice Assistant Script -->
<script src="{{ url_for('static', filename='js/assistant.js') }}"></script>
<script>
document.getElementById('saveTrigger').onclick = async () => {
    const t = document.getElementById('triggerInput').value.trim();
    if(!t) { alert('Enter a trigger phrase'); return; }
    sessionStorage.setItem('user_trigger', t);
    await fetch('/api/set_trigger', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({trigger:t})});
    alert('✓ Trigger saved and hidden from display.');
    document.getElementById('triggerInput').value = '';
};
</script>

'''
    
    new_content = content[:insert_pos] + voice_ui + content[insert_pos:]
    
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✓ Voice UI added")

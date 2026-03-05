const API_BASE_URL = 'http://127.0.0.1:5000';

// Hilfsfunktion: SHA-256-Hash einer Zeichenfolge (hex)
async function sha256(message) {
    const msgBuffer = new TextEncoder().encode(message);
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    // 1. Elemente holen
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const messageDiv = document.getElementById('message');
    const submitBtn = document.getElementById('submitBtn');

    // Sicherheitscheck: Falls ein Element im HTML fehlt
    if (!emailInput || !passwordInput || !messageDiv || !submitBtn) {
        console.error("Fehler: Ein HTML-Element wurde nicht gefunden!");
        return;
    }

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    // 2. Validierung
    if (!email) {
        showMessage('Bitte gib deine E-Mail ein.', 'error');
        return;
    }

    if (!password) {
        showMessage('Bitte gib dein Passwort ein.', 'error');
        return;
    }

    // 3. UI in Ladezustand versetzen
    submitBtn.disabled = true;
    submitBtn.textContent = 'Lade...';
    hideMessage();

    try {
        console.log(`Login Versuch für: ${email}`);

        // 4. Request an den Server
        const response = await fetch(`${API_BASE_URL}/api/users/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const data = await response.json();
        console.log('Server Antwort:', data);
        console.log('Response OK:', response.ok);

        if (!response.ok || data.status === 'error') {
            // --- FEHLER VOM SERVER ---
            throw new Error(data.message || 'Login fehlgeschlagen');
        }

        // --- ERFOLG ---
        showMessage('Login erfolgreich! Weiterleitung...', 'success');

        // Zugriff auf das verschachtelte user object
        const user = data.data;
        if (!user || !user.email) {
            throw new Error('Server hat keine E-Mail zurückgesendet');
        }

        // Benutzernamen aus E-Mail extrahieren (Teil vor dem @)
        const username = user.email.split('@')[0];

        // Benutzerdaten im Browser speichern
        localStorage.setItem('userId', user.id);
        localStorage.setItem('displayName', username);
        localStorage.setItem('email', user.email);
        // Passwort-Hash speichern für spätere API-Aufrufe
        const passwordHash = await sha256(password);
        localStorage.setItem('passwordHash', passwordHash);
            console.log('stored auth', {email: user.email, passwordHash});

        // Redirect after 1 second
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 1000);

    } catch (error) {
        // --- NETZWERK / SERVER FEHLER ---
        console.error('Login Error:', error);
        showMessage(error.message, 'error');

        // Button wieder aktivieren
        submitBtn.disabled = false;
        submitBtn.textContent = 'Anmelden';
    }
});

// ---- Hilfsfunktionen ----

function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = text;
    messageDiv.style.display = 'block';

    if (type === 'success') {
        messageDiv.style.backgroundColor = '#e8f5e9';
        messageDiv.style.color = '#2e7d32';
        messageDiv.style.border = '1px solid #a5d6a7';
    } else {
        messageDiv.style.backgroundColor = '#ffebee';
        messageDiv.style.color = '#c62828';
        messageDiv.style.border = '1px solid #ef9a9a';
    }
}

function hideMessage() {
    const messageDiv = document.getElementById('message');
    messageDiv.style.display = 'none';
    messageDiv.textContent = '';
}

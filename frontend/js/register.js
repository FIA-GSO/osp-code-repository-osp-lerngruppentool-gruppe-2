const API_BASE_URL = 'http://127.0.0.1:5000'; 

// SHA-256 helper
async function sha256(message) {
    const msgBuffer = new TextEncoder().encode(message);
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

document.getElementById('registerForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // DOM Elemente holen
    // Stelle sicher, dass diese IDs in deiner register.html existieren!
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    
    const email = emailInput.value;
    const password = passwordInput.value;
    const confirmPassword = confirmPasswordInput.value;

    const messageDiv = document.getElementById('message');
    const submitBtn = this.querySelector('button[type="submit"]');
    
    // Reset Message
    if(messageDiv) {
        messageDiv.style.display = 'none';
        messageDiv.className = '';
    }

    // 1. Client-seitige Validierung
    if (password !== confirmPassword) {
        showMessage('Die Passwörter stimmen nicht überein!', 'error');
        return;
    }

    if (password.length < 1) { // Optional: Mindestlänge
        showMessage('Das Passwort muss mindestens 1 Zeichen lang sein.', 'error');
        return;
    }

    // Button deaktivieren
    submitBtn.disabled = true;
    submitBtn.textContent = 'Registrierung läuft...';

    try {
        console.log("Sende Registrierung an:", `${API_BASE_URL}/api/users`);

        // 2. API Aufruf
        const response = await fetch(`${API_BASE_URL}/api/users`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password 
            })
        });

        const data = await response.json();
        console.log('Server Antwort (register):', data);
        console.log('Response OK:', response.ok);

        if (!response.ok || data.status === 'error') {
            throw new Error(data.message || 'Registrierung fehlgeschlagen');
        }

        // 3. Erfolgsfall
        showMessage('Registrierung erfolgreich! Du wirst weitergeleitet...', 'success');
        
        // Nutzung des verschachtelten data-Objekts analog zu login.js
        const user = data.data;
        if (!user || !user.email) {
            throw new Error('Server hat keine E-Mail zurückgesendet');
        }

        // Benutzernamen aus E-Mail extrahieren (Teil vor dem @)
        const username = user.email.split('@')[0];
        
        // WICHTIG: User ID speichern (Einheitlich mit Login.js)
        localStorage.setItem('userId', user.id);
        localStorage.setItem('displayName', username);
        localStorage.setItem('email', user.email);
        // Hash des Passworts berechnen und speichern
        const pwdHash = await sha256(password);
        localStorage.setItem('passwordHash', pwdHash);
        console.log('stored auth (register)', {email: user.email, passwordHash: pwdHash});

        // Weiterleitung zur Hauptseite
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 1500);

    } catch (error) {
        console.error('Register Error:', error);
        showMessage(error.message || 'Server nicht erreichbar.', 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Registrieren';
    }
});

// Hilfsfunktion für Nachrichten
function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    if (messageDiv) {
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
    } else {
        alert(text); 
    }
}

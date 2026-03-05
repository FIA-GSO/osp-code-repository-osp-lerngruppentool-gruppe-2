// ===========================
// KONSTANTEN & STATE
// ===========================
const API_BASE_URL = 'http://127.0.0.1:5000';

let allGroups    = [], allUsers    = [], allRequests  = [];
let filteredGroups = [], filteredUsers = [], filteredRequests = [];
let groupsPage = 1, usersPage = 1;
const PAGE_SIZE = 10;
let currentRole   = null;
let pendingDeleteFn = null;

// ===========================
// HELPERS
// ===========================

function getHeaders(includeJson = true) {
    const headers = {};
    if (includeJson) headers['Content-Type'] = 'application/json';
    const email = localStorage.getItem('email');
    const pw    = localStorage.getItem('passwordHash');
    if (email) headers['X-Auth-Email']         = email;
    if (pw)    headers['X-Auth-Password-Hash'] = pw;
    return headers;
}

function isLoggedIn() {
    return !!localStorage.getItem('email') || !!localStorage.getItem('userId');
}

function showMessage(text, type) {
    const existing = document.querySelector('.toast-msg');
    if (existing) existing.remove();

    const msg = document.createElement('div');
    msg.className = 'toast-msg';
    msg.textContent = text;
    msg.style.cssText = `
        position:fixed; top:20px; right:20px;
        padding:15px 20px; border-radius:8px; z-index:999999;
        background:${type === 'success' ? '#d4edda' : '#f8d7da'};
        color:${type === 'success' ? '#155724' : '#721c24'};
        border:1px solid ${type === 'success' ? '#c3e6cb' : '#f5c6cb'};
        font-family:sans-serif; font-size:0.9rem;
        box-shadow:0 4px 12px rgba(0,0,0,0.15);
        transition: opacity 0.3s ease;
    `;
    document.body.appendChild(msg);
    setTimeout(() => {
        msg.style.opacity = '0';
        setTimeout(() => msg.remove(), 300);
    }, 3000);
}

function formatDate(dateStr) {
    if (!dateStr) return '–';
    return new Date(dateStr).toLocaleDateString('de-DE', {
        day: '2-digit', month: '2-digit', year: 'numeric'
    });
}

function getRoleBadge(role) {
    const map = {
        admin:   { bg: '#fce4ec', color: '#c62828', label: 'Admin'   },
        teacher: { bg: '#e3f2fd', color: '#1565c0', label: 'Teacher' },
        user:    { bg: '#f3f4f6', color: '#374151', label: 'User'    }
    };
    const c = map[role] || map.user;
    return `<span class="role-badge" style="background:${c.bg};color:${c.color};">${c.label}</span>`;
}

function getStatusBadge(status) {
    const isActive = status === 'active' || status === 'aktiv';
    return `<span class="status-badge ${isActive ? 'active' : 'inactive'}">${isActive ? 'Aktiv' : 'Inaktiv'}</span>`;
}

function getRequestStatusBadge(status) {
    const map = {
        pending:  { bg: '#fff3cd', color: '#856404', label: 'Offen'     },
        approved: { bg: '#d4edda', color: '#155724', label: 'Genehmigt' },
        rejected: { bg: '#f8d7da', color: '#721c24', label: 'Abgelehnt' }
    };
    const c = map[status] || map.pending;
    return `<span class="role-badge" style="background:${c.bg};color:${c.color};">${c.label}</span>`;
}

// ===========================
// ZUGANGSKONTROLLE
// ===========================

async function checkAccess() {
    if (!isLoggedIn()) {
        window.location.href = 'login.html';
        return false;
    }

    // ✅ DEBUG - zeigt was im localStorage liegt
    console.table({
        email:       localStorage.getItem('email'),
        userId:      localStorage.getItem('userId'),
        role:        localStorage.getItem('role'),
        displayName: localStorage.getItem('displayName')
    });

    // Schritt 1: Rolle aus localStorage bereinigt lesen
    let role = (localStorage.getItem('role') || '').toLowerCase().trim();
    console.log(`📦 Rolle aus localStorage: "${role}"`);

    if (role === 'admin' || role === 'teacher') {
        currentRole = role;
        console.log(`✅ Zugang gewährt via localStorage`);
        return true;
    }

    // Schritt 2: Via userId vom Server holen
    const userId = localStorage.getItem('userId');
    const email  = localStorage.getItem('email');

    if (userId) {
        try {
            console.log(`🔍 Frage Server nach userId: ${userId}`);
            const response = await fetch(`${API_BASE_URL}/api/users/${userId}`, {
                method:  'GET',
                headers: getHeaders(true)
            });

            console.log(`Server Status: ${response.status}`);

            if (response.ok) {
                const data       = await response.json();
                console.log('Server Antwort:', data);

                // Verschiedene Response-Strukturen abfangen
                const user       = data.data || data.user || data;
                const serverRole = (user.role || '').toLowerCase().trim();

                console.log(`📡 Server-Rolle: "${serverRole}"`);
                localStorage.setItem('role', serverRole);
                currentRole = serverRole;

                if (serverRole === 'admin' || serverRole === 'teacher') {
                    console.log(`✅ Zugang gewährt via Server (userId)`);
                    return true;
                }
            }
        } catch (error) {
            console.error('❌ Fehler bei userId-Abfrage:', error);
        }
    }

    // Schritt 3: Fallback - alle User laden und eigenen per E-Mail finden
    if (email) {
        try {
            console.log(`🔍 Fallback: Suche User per E-Mail "${email}"`);
            const response = await fetch(
                `${API_BASE_URL}/api/users?limit=1000&offset=0`,
                { method: 'GET', headers: getHeaders(true) }
            );

            if (response.ok) {
                const data    = await response.json();
                const payload = data.data || data;
                const users   = payload.users || payload || [];
                const me      = users.find(u =>
                    (u.email || '').toLowerCase() === email.toLowerCase()
                );

                if (me) {
                    const serverRole = (me.role || '').toLowerCase().trim();
                    console.log(`📡 Gefundene Rolle via Userliste: "${serverRole}"`);
                    localStorage.setItem('role',   serverRole);
                    localStorage.setItem('userId', me.id);
                    currentRole = serverRole;

                    if (serverRole === 'admin' || serverRole === 'teacher') {
                        console.log(`✅ Zugang gewährt via Userliste`);
                        return true;
                    }
                } else {
                    console.warn('❌ User nicht in der Liste gefunden');
                }
            }
        } catch (error) {
            console.error('❌ Fehler beim Fallback:', error);
        }
    }

    console.warn('❌ Kein Zugang möglich');
    showAccessDenied();
    return false;
}

function showAccessDenied() {
    document.getElementById('accessDenied').style.display = 'flex';
    document.getElementById('adminContent').style.display = 'none';
}

function showAdminContent() {
    document.getElementById('accessDenied').style.display = 'none';
    document.getElementById('adminContent').style.display = 'block';
}

// ===========================
// API CALLS
// ===========================

async function apiFetch(url, options = {}) {
    const response = await fetch(url, {
        headers: getHeaders(true),
        ...options
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
}

async function fetchAllGroups() {
    try {
        const data     = await apiFetch(`${API_BASE_URL}/api/groups?limit=1000&offset=0`);
        const payload  = data.data || data;
        allGroups      = payload.groups || [];
        filteredGroups = [...allGroups];
        return allGroups;
    } catch (e) {
        console.error(e);
        showMessage('Fehler beim Laden der Gruppen', 'error');
        return [];
    }
}

async function fetchAllUsers() {
    try {
        const data    = await apiFetch(`${API_BASE_URL}/api/users?limit=1000&offset=0`);
        const payload = data.data || data;
        allUsers      = payload.users || payload || [];
        filteredUsers = [...allUsers];
        return allUsers;
    } catch (e) {
        console.error(e);
        showMessage('Fehler beim Laden der Benutzer', 'error');
        return [];
    }
}

async function fetchAllRequests(status = 'pending') {
    try {
        const params = new URLSearchParams({ limit: '1000', offset: '0' });
        if (status) params.append('status', status);
        const data       = await apiFetch(`${API_BASE_URL}/api/join-requests?${params}`);
        const payload    = data.data || data;
        allRequests      = payload.requests || payload || [];
        filteredRequests = [...allRequests];
        return allRequests;
    } catch (e) {
        console.error(e);
        showMessage('Fehler beim Laden der Beitrittsanfragen', 'error');
        return [];
    }
}

async function deleteGroup(groupId) {
    try {
        await apiFetch(`${API_BASE_URL}/api/groups/${groupId}`, { method: 'DELETE' });
        showMessage('Gruppe erfolgreich gelöscht!', 'success');
        return true;
    } catch (e) {
        showMessage('Fehler beim Löschen der Gruppe', 'error');
        return false;
    }
}

async function deleteUser(userId) {
    try {
        await apiFetch(`${API_BASE_URL}/api/users/${userId}`, { method: 'DELETE' });
        showMessage('Benutzer erfolgreich gelöscht!', 'success');
        return true;
    } catch (e) {
        showMessage('Fehler beim Löschen des Benutzers', 'error');
        return false;
    }
}

async function respondToRequest(requestId, action) {
    try {
        await apiFetch(
            `${API_BASE_URL}/api/join-requests/${requestId}/${action}`,
            { method: 'POST' }
        );
        showMessage(
            action === 'approve' ? 'Anfrage genehmigt!' : 'Anfrage abgelehnt!',
            'success'
        );
        return true;
    } catch (e) {
        showMessage('Fehler beim Bearbeiten der Anfrage', 'error');
        return false;
    }
}

// ===========================
// STATS
// ===========================

function updateStats() {
    const activeGroups   = allGroups.filter(g => g.status === 'active' || g.status === 'aktiv').length;
    const reportedGroups = allGroups.filter(g => (g.reports || 0) > 0).length;
    const pendingReqs    = allRequests.filter(r => r.status === 'pending').length;

    document.getElementById('statUsers').textContent           = allUsers.length;
    document.getElementById('statGroups').textContent          = allGroups.length;
    document.getElementById('statActiveGroups').textContent    = activeGroups;
    document.getElementById('statPendingRequests').textContent = pendingReqs;
    document.getElementById('statReports').textContent         = reportedGroups;

    const badge = document.getElementById('requestsBadge');
    badge.textContent   = pendingReqs;
    badge.style.display = pendingReqs > 0 ? 'inline-block' : 'none';
}

// ===========================
// PAGINATION BUILDER
// ===========================

function buildPagination(containerId, page, total, onPageChange) {
    const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
    const container  = document.getElementById(containerId);
    container.innerHTML = '';

    for (let i = 1; i <= Math.min(totalPages, 5); i++) {
        const btn = document.createElement('button');
        btn.className   = `page-number${i === page ? ' active' : ''}`;
        btn.textContent = i;
        btn.addEventListener('click', () => onPageChange(i));
        container.appendChild(btn);
    }
    return totalPages;
}

// ===========================
// GRUPPEN TABELLE
// ===========================

function renderGroupsTable() {
    const tbody = document.getElementById('groupsTableBody');
    const total = filteredGroups.length;

    if (total === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" class="table-empty">
                    <i class="pi pi-inbox"></i>
                    <p>Keine Gruppen gefunden</p>
                </td>
            </tr>`;
        document.getElementById('groupsPaginationInfo').textContent = 'Keine Gruppen';
        document.getElementById('groupsPrevBtn').disabled = true;
        document.getElementById('groupsNextBtn').disabled = true;
        return;
    }

    const start  = (groupsPage - 1) * PAGE_SIZE;
    const groups = filteredGroups.slice(start, start + PAGE_SIZE);

    tbody.innerHTML = groups.map(g => {
        const title = g.title || g.name || '–';
        const type  = g.type  || '–';
        return `
            <tr>
                <td class="td-id">${g.id}</td>
                <td class="td-title">
                    <strong>${title}</strong>
                    ${g.description
                        ? `<br><small class="td-sub">${g.description.substring(0, 50)}...</small>`
                        : ''}
                </td>
                <td>${g.subject || '–'}</td>
                <td>
                    <span class="type-badge ${type}">
                        <i class="pi pi-${type === 'online' ? 'globe' : 'map-marker'}"></i>
                        ${type}
                    </span>
                </td>
                <td>${g.class || '–'}</td>
                <td class="td-center">
                    <i class="pi pi-users" style="color:#667eea;"></i>
                    ${g.member_count || 0}${g.max_users ? '/' + g.max_users : ''}
                </td>
                <td>${getStatusBadge(g.status)}</td>
                <td>${formatDate(g.created_at || g.createdAt)}</td>
                <td class="td-center">
                    ${(g.reports || 0) > 0
                        ? `<span class="report-badge">${g.reports}</span>`
                        : `<span style="color:#aaa;">0</span>`}
                </td>
                <td>
                    <div class="action-btns">
                        <button class="action-btn info" title="Details"
                            onclick="showGroupDetail(${g.id})">
                            <i class="pi pi-eye"></i>
                        </button>
                        <button class="action-btn danger" title="Löschen"
                            onclick="confirmDelete('group', ${g.id}, '${title.replace(/'/g, "\\'")}')">
                            <i class="pi pi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>`;
    }).join('');

    const totalPages = buildPagination('groupsPageNumbers', groupsPage, total, (i) => {
        groupsPage = i;
        renderGroupsTable();
    });

    const end = Math.min(start + PAGE_SIZE, total);
    document.getElementById('groupsPaginationInfo').textContent =
        `Zeige ${start + 1}–${end} von ${total} Gruppen`;
    document.getElementById('groupsPrevBtn').disabled = groupsPage <= 1;
    document.getElementById('groupsNextBtn').disabled = groupsPage >= totalPages;
}

// ===========================
// BENUTZER TABELLE
// ===========================

function renderUsersTable() {
    const tbody  = document.getElementById('usersTableBody');
    const total  = filteredUsers.length;
    const selfId = localStorage.getItem('userId');

    if (total === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="table-empty">
                    <i class="pi pi-inbox"></i>
                    <p>Keine Benutzer gefunden</p>
                </td>
            </tr>`;
        document.getElementById('usersPaginationInfo').textContent = 'Keine Benutzer';
        document.getElementById('usersPrevBtn').disabled = true;
        document.getElementById('usersNextBtn').disabled = true;
        return;
    }

    const start = (usersPage - 1) * PAGE_SIZE;
    const users = filteredUsers.slice(start, start + PAGE_SIZE);

    tbody.innerHTML = users.map(u => {
        const email  = u.email || '–';
        const isSelf = String(u.id) === String(selfId);
        return `
            <tr ${isSelf ? 'class="self-row"' : ''}>
                <td class="td-id">${u.id}</td>
                <td>
                    ${email}
                    ${isSelf ? '<span class="self-badge">Du</span>' : ''}
                </td>
                <td>${getRoleBadge(u.role || 'user')}</td>
                <td class="td-center">${u.group_count || u.groupCount || '–'}</td>
                <td>
                    <div class="action-btns">
                        ${!isSelf
                            ? `<button class="action-btn danger" title="Löschen"
                                onclick="confirmDelete('user', ${u.id}, '${email.replace(/'/g, "\\'")}')">
                                <i class="pi pi-trash"></i>
                               </button>`
                            : '<span style="color:#aaa;font-size:0.8rem;">–</span>'}
                    </div>
                </td>
            </tr>`;
    }).join('');

    const totalPages = buildPagination('usersPageNumbers', usersPage, total, (i) => {
        usersPage = i;
        renderUsersTable();
    });

    const end = Math.min(start + PAGE_SIZE, total);
    document.getElementById('usersPaginationInfo').textContent =
        `Zeige ${start + 1}–${end} von ${total} Benutzern`;
    document.getElementById('usersPrevBtn').disabled = usersPage <= 1;
    document.getElementById('usersNextBtn').disabled = usersPage >= totalPages;
}

// ===========================
// ANFRAGEN TABELLE
// ===========================

function renderRequestsTable() {
    const tbody = document.getElementById('requestsTableBody');

    if (filteredRequests.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="table-empty">
                    <i class="pi pi-inbox"></i>
                    <p>Keine Anfragen gefunden</p>
                </td>
            </tr>`;
        return;
    }

    tbody.innerHTML = filteredRequests.map(req => {
        const message   = req.message || '–';
        const status    = req.status  || 'pending';
        const isPending = status === 'pending';
        return `
            <tr>
                <td class="td-id">${req.id}</td>
                <td>User #${req.user_id  || req.userId  || '–'}</td>
                <td>Gruppe #${req.group_id || req.groupId || '–'}</td>
                <td class="td-message">
                    <span title="${message}">
                        ${message.length > 40
                            ? message.substring(0, 40) + '...'
                            : message}
                    </span>
                </td>
                <td>${getRequestStatusBadge(status)}</td>
                <td>${formatDate(req.created_at || req.createdAt)}</td>
                <td>
                    <div class="action-btns">
                        ${isPending ? `
                            <button class="action-btn success" title="Genehmigen"
                                onclick="handleRequest(${req.id}, 'approve')">
                                <i class="pi pi-check"></i>
                            </button>
                            <button class="action-btn danger" title="Ablehnen"
                                onclick="handleRequest(${req.id}, 'reject')">
                                <i class="pi pi-times"></i>
                            </button>`
                        : '<span style="color:#aaa;font-size:0.8rem;">–</span>'}
                    </div>
                </td>
            </tr>`;
    }).join('');
}

// ===========================
// GRUPPEN DETAIL MODAL
// ===========================

function showGroupDetail(groupId) {
    const g = allGroups.find(g => g.id === groupId);
    if (!g) return;

    document.getElementById('modalGroupTitle').textContent = g.title || g.name || '–';
    document.getElementById('groupModalBody').innerHTML = `
        <div class="modal-detail-grid">
            ${[
                ['ID',            g.id],
                ['Status',        getStatusBadge(g.status)],
                ['Fach',          g.subject  || '–'],
                ['Thema',         g.topic    || '–'],
                ['Typ',           g.type     || '–'],
                ['Ort',           g.location || '–'],
                ['Klasse',        g.class    || '–'],
                ['Mitglieder',    `${g.member_count || 0} / ${g.max_users || '∞'}`],
                ['Meldungen',     (g.reports || 0) > 0
                    ? `<span class="report-badge">${g.reports}</span>` : '0'],
                ['Erstellt am',   formatDate(g.created_at     || g.createdAt)],
                ['Zuletzt aktiv', formatDate(g.last_active_at || g.lastActiveAt)],
            ].map(([label, value]) => `
                <div class="modal-detail-item">
                    <span class="modal-detail-label">${label}</span>
                    <span class="modal-detail-value">${value}</span>
                </div>`).join('')}
        </div>
        <div class="modal-description">
            <span class="modal-detail-label">Beschreibung</span>
            <p>${g.description || 'Keine Beschreibung'}</p>
        </div>
    `;

    document.getElementById('groupDetailModal').style.display = 'flex';
}

// ===========================
// CONFIRM DELETE
// ===========================

function confirmDelete(type, id, name) {
    const label = type === 'group' ? 'Gruppe' : 'Benutzer';
    document.getElementById('confirmDeleteText').innerHTML =
        `${label} "<strong>${name}</strong>" (ID: ${id}) wirklich löschen?`;
    document.getElementById('confirmDeleteModal').style.display = 'flex';

    pendingDeleteFn = async () => {
        const success = type === 'group'
            ? await deleteGroup(id)
            : await deleteUser(id);

        if (!success) return;

        if (type === 'group') {
            allGroups      = allGroups.filter(g => g.id !== id);
            filteredGroups = filteredGroups.filter(g => g.id !== id);
            renderGroupsTable();
        } else {
            allUsers      = allUsers.filter(u => u.id !== id);
            filteredUsers = filteredUsers.filter(u => u.id !== id);
            renderUsersTable();
        }
        updateStats();
    };
}

// ===========================
// ANFRAGEN BEARBEITEN
// ===========================

async function handleRequest(requestId, action) {
    const success = await respondToRequest(requestId, action);
    if (!success) return;

    const req = allRequests.find(r => r.id === requestId);
    if (req) req.status = action === 'approve' ? 'approved' : 'rejected';

    applyRequestFilter(document.getElementById('requestStatusFilter').value);
    updateStats();
}

// ===========================
// FILTER & SUCHE
// ===========================

function applyGroupFilter() {
    const search = document.getElementById('groupSearchInput').value.toLowerCase().trim();
    const status = document.getElementById('groupStatusFilter').value;

    filteredGroups = allGroups.filter(g => {
        const title   = (g.title || g.name || '').toLowerCase();
        const subject = (g.subject || '').toLowerCase();
        return (!search || title.includes(search) || subject.includes(search))
            && (!status || g.status === status);
    });

    groupsPage = 1;
    renderGroupsTable();
}

function applyUserFilter() {
    const search = document.getElementById('userSearchInput').value.toLowerCase().trim();
    const role   = document.getElementById('userRoleFilter').value;

    filteredUsers = allUsers.filter(u => {
        const email = (u.email || '').toLowerCase();
        return (!search || email.includes(search))
            && (!role || u.role === role);
    });

    usersPage = 1;
    renderUsersTable();
}

function applyRequestFilter(status) {
    filteredRequests = status
        ? allRequests.filter(r => r.status === status)
        : [...allRequests];
    renderRequestsTable();
}

// ===========================
// TABS
// ===========================

function setupTabs() {
    document.querySelectorAll('.admin-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.admin-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(`tab-${tab.dataset.tab}`).classList.add('active');
        });
    });
}

// ===========================
// AVATAR DROPDOWN & LOGOUT
// ===========================

function setupAvatarDropdown() {
    const avatar   = document.getElementById('userAvatar');
    const dropdown = document.getElementById('avatarDropdown');

    document.getElementById('avatarDropdownName').textContent  =
        localStorage.getItem('displayName') || 'Benutzer';
    document.getElementById('avatarDropdownEmail').textContent =
        localStorage.getItem('email') || '';

    avatar.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('open');
    });

    document.addEventListener('click', (e) => {
        if (!avatar.contains(e.target)) dropdown.classList.remove('open');
    });

    document.getElementById('logoutBtn').addEventListener('click', () => {
        localStorage.clear();
        window.location.href = 'login.html';
    });
}

// ===========================
// USER INFO
// ===========================

function loadUserInfo() {
    const name  = localStorage.getItem('displayName');
    const email = localStorage.getItem('email');
    const label = document.getElementById('userNameLabel');
    if (label) label.textContent = name || (email ? email.split('@')[0] : 'Benutzer');
}

// ===========================
// EVENT LISTENERS
// ===========================

function setupEventListeners() {

    // Gruppen Suche & Filter
    let gTimeout;
    document.getElementById('groupSearchInput').addEventListener('input', () => {
        clearTimeout(gTimeout);
        gTimeout = setTimeout(applyGroupFilter, 300);
    });
    document.getElementById('groupStatusFilter').addEventListener('change', applyGroupFilter);

    // Gruppen Pagination
    document.getElementById('groupsPrevBtn').addEventListener('click', () => {
        if (groupsPage > 1) { groupsPage--; renderGroupsTable(); }
    });
    document.getElementById('groupsNextBtn').addEventListener('click', () => {
        if (groupsPage < Math.ceil(filteredGroups.length / PAGE_SIZE)) {
            groupsPage++;
            renderGroupsTable();
        }
    });

    // Benutzer Suche & Filter
    let uTimeout;
    document.getElementById('userSearchInput').addEventListener('input', () => {
        clearTimeout(uTimeout);
        uTimeout = setTimeout(applyUserFilter, 300);
    });
    document.getElementById('userRoleFilter').addEventListener('change', applyUserFilter);

    // Benutzer Pagination
    document.getElementById('usersPrevBtn').addEventListener('click', () => {
        if (usersPage > 1) { usersPage--; renderUsersTable(); }
    });
    document.getElementById('usersNextBtn').addEventListener('click', () => {
        if (usersPage < Math.ceil(filteredUsers.length / PAGE_SIZE)) {
            usersPage++;
            renderUsersTable();
        }
    });

    // Anfragen Filter
    document.getElementById('requestStatusFilter').addEventListener('change', (e) => {
        applyRequestFilter(e.target.value);
    });

    // Gruppen Detail Modal
    const groupDetailModal = document.getElementById('groupDetailModal');
    document.getElementById('closeGroupModal').addEventListener('click', () => {
        groupDetailModal.style.display = 'none';
    });
    groupDetailModal.addEventListener('click', (e) => {
        if (e.target === groupDetailModal) groupDetailModal.style.display = 'none';
    });

    // Confirm Delete Modal
    const confirmModal = document.getElementById('confirmDeleteModal');
    document.getElementById('cancelDeleteBtn').addEventListener('click', () => {
        confirmModal.style.display = 'none';
        pendingDeleteFn = null;
    });
    document.getElementById('confirmDeleteBtn').addEventListener('click', async () => {
        if (pendingDeleteFn) await pendingDeleteFn();
        pendingDeleteFn = null;
        confirmModal.style.display = 'none';
    });
    confirmModal.addEventListener('click', (e) => {
        if (e.target === confirmModal) {
            confirmModal.style.display = 'none';
            pendingDeleteFn = null;
        }
    });

    // ESC schließt alle Modals
    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape') return;
        document.getElementById('groupDetailModal').style.display   = 'none';
        document.getElementById('confirmDeleteModal').style.display = 'none';
        pendingDeleteFn = null;
    });
}

// ===========================
// INIT
// ===========================

document.addEventListener('DOMContentLoaded', async () => {
    loadUserInfo();

    const hasAccess = await checkAccess();
    if (!hasAccess) return;

    showAdminContent();

    await Promise.all([
        fetchAllGroups(),
        fetchAllUsers(),
        fetchAllRequests('pending')
    ]);

    updateStats();
    renderGroupsTable();
    renderUsersTable();
    renderRequestsTable();
    setupTabs();
    setupAvatarDropdown();
    setupEventListeners();
});

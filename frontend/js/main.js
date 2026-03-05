// ===========================
// KONSTANTEN & STATE
// ===========================
const API_BASE_URL = 'http://127.0.0.1:5000';

let currentUser    = null;
let allGroups      = [];
let filteredGroups = [];
let totalGroups    = 0;
let myGroupIds     = new Set();

// Pagination State
let currentPage = 1;
let pageSize    = 8;

// Filter State
let activeFilters = {
    subjects:       [],
    learningFields: []
};

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
    const existing = document.querySelector('.toast-message');
    if (existing) existing.remove();

    const msg = document.createElement('div');
    msg.className = 'toast-message';
    msg.textContent = text;
    msg.style.cssText = `
        position: fixed; top: 20px; right: 20px;
        padding: 15px 20px; border-radius: 8px; z-index: 99999;
        background-color: ${type === 'success' ? '#d4edda' : '#f8d7da'};
        color:            ${type === 'success' ? '#155724' : '#721c24'};
        border: 1px solid ${type === 'success' ? '#c3e6cb' : '#f5c6cb'};
        font-family: sans-serif; font-size: 0.9rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    document.body.appendChild(msg);
    setTimeout(() => {
        msg.style.opacity = '0';
        msg.style.transition = 'opacity 0.3s ease';
        setTimeout(() => msg.remove(), 300);
    }, 3000);
}

// ===========================
// API CALLS
// ===========================

async function fetchGroups(search = '') {
    try {
        if (!isLoggedIn()) {
            window.location.href = 'login.html';
            return;
        }

        const params = new URLSearchParams({ limit: '1000', offset: '0' });
        if (search) params.append('search', search);

        const response = await fetch(`${API_BASE_URL}/api/groups?${params}`, {
            method:  'GET',
            headers: getHeaders(true)
        });

        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                localStorage.clear();
                window.location.href = 'login.html';
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data    = await response.json();
        const payload = data.data || data;
        const groups  = payload.groups || [];

        // ✅ member_count ist bereits im Response enthalten
        allGroups = groups.map(group => ({
            ...group,
            member_count: group.member_count ?? 0,
            memberCount:  group.member_count ?? 0
        }));

        filteredGroups = [...allGroups];
        totalGroups    = allGroups.length;

    } catch (error) {
        console.error('Fehler beim Laden der Gruppen:', error);
        showMessage(error.message || 'Fehler beim Laden der Gruppen', 'error');
    }
}

async function fetchMyGroups() {
    const userId = localStorage.getItem('userId');
    if (!userId) return;

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/users/${userId}/groups`,
            { method: 'GET', headers: getHeaders(true) }
        );

        if (!response.ok) return;

        const data    = await response.json();
        const payload = data.data || data;
        const groups  = payload.groups || payload || [];

        myGroupIds = new Set(groups.map(g => String(g.id || g.group_id)));

    } catch (error) {
        console.error('Fehler beim Laden eigener Gruppen:', error);
    }
}

// ✅ Member Count von API holen
async function fetchMemberCount(groupId) {
    try {
        const response = await fetch(
            `${API_BASE_URL}/api/groups/${groupId}/members/count`,
            { method: 'GET', headers: getHeaders(true) }
        );
        if (!response.ok) return 0;
        const data = await response.json();
        return data.data?.member_count ?? 0;
    } catch {
        return 0;
    }
}

// ✅ Karte im Grid mit neuem Count aktualisieren
function updateCardMemberCount(groupId) {
    const card = document.querySelector(`.group-card[data-group-id="${groupId}"]`);
    if (!card) return;

    const group = allGroups.find(g => String(g.id) === String(groupId));
    if (!group) return;

    const span = card.querySelector('.user-info span');
    if (span) span.textContent = `${group.member_count} Mitglieder`;
}

// ✅ Gruppe beitreten (public)
async function addMemberToGroup(groupId, userId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/groups/${groupId}/members`, {
            method:  'POST',
            headers: getHeaders(true),
            body:    JSON.stringify({ user_id: parseInt(userId), role: 'member' })
        });

        const result = await response.json();

        if (!response.ok || result.status === 'error') {
            throw new Error(result.message || `HTTP ${response.status}`);
        }

        // ✅ Lokal als Mitglied merken
        myGroupIds.add(String(groupId));

        // ✅ Echten Member Count von der API holen
        const newCount = await fetchMemberCount(groupId);

        // ✅ In beiden Arrays aktualisieren
        const groupInAll      = allGroups.find(g => String(g.id) === String(groupId));
        const groupInFiltered = filteredGroups.find(g => String(g.id) === String(groupId));

        if (groupInAll) {
            groupInAll.member_count = newCount;
            groupInAll.memberCount  = newCount;
        }
        if (groupInFiltered) {
            groupInFiltered.member_count = newCount;
            groupInFiltered.memberCount  = newCount;
        }

        // ✅ Karte im DOM sofort updaten
        updateCardMemberCount(groupId);

        showMessage('Erfolgreich der Gruppe beigetreten!', 'success');
        return result;

    } catch (error) {
        console.error('Fehler beim Beitreten:', error);
        showMessage(error.message || 'Fehler beim Beitreten der Gruppe', 'error');
        return null;
    }
}

// ✅ Beitrittsanfrage senden (private)
async function createJoinRequest(groupId, userId, message = null) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/join-requests`, {
            method:  'POST',
            headers: getHeaders(true),
            body:    JSON.stringify({
                groupId: parseInt(groupId),
                userId:  parseInt(userId),
                message
            })
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.message || `HTTP ${response.status}`);
        }

        showMessage('Beitrittsanfrage wurde gesendet!', 'success');
        return await response.json();

    } catch (error) {
        console.error('Fehler bei Anfrage:', error);
        showMessage(error.message || 'Fehler beim Senden der Beitrittsanfrage', 'error');
        return null;
    }
}

async function createGroup(groupData) {
    try {
        const userId = localStorage.getItem('userId');
        if (!userId) throw new Error('Kein Benutzer angemeldet');

        const payload = {
            organiser_id: parseInt(userId),
            title:        groupData.name,
            subject:      groupData.subject,
            topic:        groupData.learningField,
            description:  groupData.description || null,
            type:         groupData.type         || 'online',
            location:     groupData.location     || null,
            class:        groupData.className    || null,
            max_users:    groupData.maxUsers ? parseInt(groupData.maxUsers) : null,
            status:       'active'
        };

        const response = await fetch(`${API_BASE_URL}/api/groups`, {
            method:  'POST',
            headers: getHeaders(true),
            body:    JSON.stringify(payload)
        });

        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.message || `HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        // ✅ Gruppen neu laden — KEIN Loop, nur einmaliger Call
        await fetchGroups();
        await fetchMyGroups();
        applyFilters();

        currentPage = getTotalPages();
        renderCurrentPage();

        showMessage(`Gruppe "${groupData.name}" wurde erfolgreich erstellt!`, 'success');
        return result;

    } catch (error) {
        console.error('Fehler beim Erstellen:', error);
        showMessage(error.message || 'Fehler beim Erstellen der Gruppe', 'error');
        return null;
    }
}

// ===========================
// PAGINATION
// ===========================

function getTotalPages() {
    return Math.max(1, Math.ceil(filteredGroups.length / pageSize));
}

function renderCurrentPage() {
    const totalPages = getTotalPages();

    if (currentPage > totalPages) currentPage = totalPages;
    if (currentPage < 1)          currentPage = 1;

    const start  = (currentPage - 1) * pageSize;
    const end    = start + pageSize;
    const groups = filteredGroups.slice(start, end);

    renderCards(groups);
    updatePaginationUI(totalPages, start, end);
}

function updatePaginationUI(totalPages, start, end) {
    const wrapper  = document.getElementById('paginationWrapper');
    const infoElem = document.getElementById('paginationInfo');

    wrapper.style.display = filteredGroups.length > pageSize ? 'flex' : 'none';

    const actualEnd = Math.min(end, filteredGroups.length);
    infoElem.textContent = filteredGroups.length > 0
        ? `Zeige ${start + 1}–${actualEnd} von ${filteredGroups.length} Gruppen`
        : 'Keine Gruppen gefunden';

    document.getElementById('firstPageBtn').disabled = currentPage === 1;
    document.getElementById('prevPageBtn').disabled  = currentPage === 1;
    document.getElementById('nextPageBtn').disabled  = currentPage >= totalPages;
    document.getElementById('lastPageBtn').disabled  = currentPage >= totalPages;

    renderPageNumbers(totalPages);
}

function renderPageNumbers(totalPages) {
    const container = document.getElementById('pageNumbers');
    container.innerHTML = '';

    if (totalPages <= 1) return;

    let startPage = Math.max(1, currentPage - 2);
    let endPage   = Math.min(totalPages, startPage + 4);

    if (endPage - startPage < 4) startPage = Math.max(1, endPage - 4);

    for (let i = startPage; i <= endPage; i++) {
        const btn = document.createElement('button');
        btn.className   = `page-number${i === currentPage ? ' active' : ''}`;
        btn.textContent = i;
        btn.addEventListener('click', () => {
            currentPage = i;
            renderCurrentPage();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
        container.appendChild(btn);
    }
}

function setupPagination() {
    document.getElementById('firstPageBtn').addEventListener('click', () => {
        currentPage = 1;
        renderCurrentPage();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    document.getElementById('prevPageBtn').addEventListener('click', () => {
        if (currentPage > 1) { currentPage--; renderCurrentPage(); window.scrollTo({ top: 0, behavior: 'smooth' }); }
    });
    document.getElementById('nextPageBtn').addEventListener('click', () => {
        if (currentPage < getTotalPages()) { currentPage++; renderCurrentPage(); window.scrollTo({ top: 0, behavior: 'smooth' }); }
    });
    document.getElementById('lastPageBtn').addEventListener('click', () => {
        currentPage = getTotalPages();
        renderCurrentPage();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    document.getElementById('pageSizeSelect').addEventListener('change', function () {
        pageSize    = parseInt(this.value);
        currentPage = 1;
        renderCurrentPage();
    });
}

// ===========================
// KARTEN RENDERN
// ===========================

function renderCards(groups) {
    const cardGrid = document.getElementById('cardGrid');
    cardGrid.innerHTML = '';

    if (groups.length === 0) {
        cardGrid.innerHTML = `
            <div style="
                color: white; text-align: center; width: 100%; margin-top: 60px;
                display: flex; flex-direction: column; align-items: center; gap: 12px;">
                <i class="pi pi-inbox" style="font-size: 3rem; opacity: 0.6;"></i>
                <p style="margin:0; font-size: 1.1rem; opacity: 0.8;">Keine Gruppen gefunden</p>
            </div>`;
        return;
    }

    groups.forEach(group => cardGrid.appendChild(createGroupCard(group)));
}

function createGroupCard(group) {
    const card = document.createElement('div');
    card.className       = 'group-card';
    card.dataset.groupId = group.id;

    const title       = group.title || group.name || 'Keine Bezeichnung';
    const description = group.description || 'Keine Beschreibung';
    const type        = group.type || 'Unbekannt';
    const location    = group.location || 'Nicht angegeben';
    const status      = group.status || 'active';
    const memberCount = group.member_count ?? group.memberCount ?? 0;
    const isActive    = status === 'active' || status === 'aktiv';

    card.innerHTML = `
        <div class="card-header">
            <h2 class="group-name">${title}</h2>
            <span class="card-status ${isActive ? 'active' : 'inactive'}">
                ${isActive ? 'Aktiv' : 'Inaktiv'}
            </span>
        </div>
        <div class="card-description">
            <p>${description.length > 80 ? description.substring(0, 80) + '...' : description}</p>
        </div>
        <div class="info-section">
            <p class="label">Fach</p>
            <p class="value">${group.subject || 'Nicht angegeben'}</p>
        </div>
        <div class="info-section">
            <p class="label">Thema</p>
            <p class="value">${group.topic || 'Nicht angegeben'}</p>
        </div>
        <div class="info-section">
            <p class="label">Typ & Ort</p>
            <p class="value">
                <i class="pi pi-${type === 'online' ? 'globe' : 'map-marker'}"></i>
                ${type} – ${location}
            </p>
        </div>
        <div class="card-footer">
            <div class="user-info">
                <i class="pi pi-users"></i>
                <span>${memberCount} Mitglieder</span>
            </div>
            <i class="pi pi-eye join-icon" title="Details anzeigen"></i>
        </div>
    `;

    card.addEventListener('click', () => showGroupDetails(group));
    card.querySelector('.join-icon').addEventListener('click', (e) => {
        e.stopPropagation();
        showGroupDetails(group);
    });

    return card;
}

// ===========================
// DETAILS MODAL
// ===========================

function showGroupDetails(group) {
    const existing = document.querySelector('.group-details-modal');
    if (existing) existing.remove();

    const modal = document.createElement('div');
    modal.className = 'group-details-modal';

    const createdDate = (group.created_at || group.createdAt)
        ? new Date(group.created_at || group.createdAt).toLocaleDateString('de-DE')
        : 'Unbekannt';

    const title       = group.title || group.name || 'Gruppe ohne Namen';
    const description = group.description || 'Keine Beschreibung hinzugefügt.';
    const subject     = group.subject || 'Nicht angegeben';
    const topic       = group.topic || 'Nicht angegeben';
    const type        = group.type || 'Unbekannt';
    const location    = group.location || 'Nicht angegeben';
    const status      = group.status || 'active';
    const memberCount = group.member_count ?? group.memberCount ?? 0;
    const maxUsers    = group.max_users || group.maxUsers;
    const className   = group.class || group.className || 'Nicht angegeben';
    const isActive    = status === 'active' || status === 'aktiv';
    const isMember    = myGroupIds.has(String(group.id));

    modal.innerHTML = `
        <div class="group-details-overlay"></div>
        <div class="group-details-content">
            <button class="group-details-close" id="closeGroupDetails">
                <i class="pi pi-times"></i>
            </button>
            <div class="group-details-header">
                <h1>${title}</h1>
                <span class="group-details-badge ${isActive ? 'active' : 'inactive'}">
                    ${isActive ? '✓ Aktiv' : '✗ Inaktiv'}
                </span>
            </div>
            <div class="group-details-description">
                <h3>Beschreibung</h3>
                <p>${description}</p>
            </div>
            <div class="group-details-info">
                <div class="detail-row">
                    <div class="detail-item">
                        <p class="detail-label">Fach</p>
                        <p class="detail-value">${subject}</p>
                    </div>
                    <div class="detail-item">
                        <p class="detail-label">Thema</p>
                        <p class="detail-value">${topic}</p>
                    </div>
                    <div class="detail-item">
                        <p class="detail-label">Klasse</p>
                        <p class="detail-value">${className}</p>
                    </div>
                    <div class="detail-item">
                        <p class="detail-label">Typ</p>
                        <p class="detail-value">${type}</p>
                    </div>
                    <div class="detail-item">
                        <p class="detail-label">Ort</p>
                        <p class="detail-value">${location}</p>
                    </div>
                    <div class="detail-item">
                        <p class="detail-label">Mitglieder</p>
                        <p class="detail-value" id="modalMemberCount">
                            ${memberCount}${maxUsers ? ' / ' + maxUsers : ''}
                        </p>
                    </div>
                    <div class="detail-item">
                        <p class="detail-label">Erstellt am</p>
                        <p class="detail-value">${createdDate}</p>
                    </div>
                </div>
            </div>
            <div class="group-details-actions">
                <button
                    class="details-btn-join ${isMember ? 'is-member' : ''}"
                    id="detailsJoinBtn"
                    ${isMember ? 'disabled' : ''}>
                    <i class="pi ${isMember ? 'pi-check' : 'pi-user-plus'}"></i>
                    ${isMember ? 'Bereits Mitglied' : 'Beitreten'}
                </button>
                <button class="details-btn-close" id="closeGroupDetailsBtn">Schließen</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    const closeModal = () => modal.remove();
    document.getElementById('closeGroupDetails').addEventListener('click', closeModal);
    document.getElementById('closeGroupDetailsBtn').addEventListener('click', closeModal);
    modal.querySelector('.group-details-overlay').addEventListener('click', closeModal);

    // ✅ { once: true } verhindert mehrfache Listener
    document.getElementById('detailsJoinBtn').addEventListener('click', async (e) => {
        e.stopPropagation();
        const btn = document.getElementById('detailsJoinBtn');
        btn.disabled  = true;
        btn.innerHTML = '<i class="pi pi-spin pi-spinner"></i> Wird beigetreten...';

        await handleJoinGroup(group.id, group.type);

        if (myGroupIds.has(String(group.id))) {
            btn.classList.add('is-member');
            btn.innerHTML = '<i class="pi pi-check"></i> Bereits Mitglied';

            // ✅ Modal Count updaten
            const modalCount = document.getElementById('modalMemberCount');
            if (modalCount) {
                const grp = allGroups.find(g => String(g.id) === String(group.id));
                if (grp) {
                    modalCount.textContent = `${grp.member_count}${maxUsers ? ' / ' + maxUsers : ''}`;
                }
            }

            // ✅ Karte updaten
            updateCardMemberCount(group.id);

        } else {
            btn.disabled  = false;
            btn.innerHTML = '<i class="pi pi-user-plus"></i> Beitreten';
        }
    }, { once: true });

    const handleKey = (e) => {
        if (e.key === 'Escape') {
            closeModal();
            document.removeEventListener('keydown', handleKey);
        }
    };
    document.addEventListener('keydown', handleKey);
}

// ===========================
// JOIN GROUP
// ===========================

async function handleJoinGroup(groupId, visibility) {
    const userId = localStorage.getItem('userId');
    if (!userId) {
        showMessage('Bitte melde dich zuerst an', 'error');
        return;
    }

    if (myGroupIds.has(String(groupId))) {
        showMessage('Du bist bereits Mitglied dieser Gruppe', 'error');
        return;
    }

    if (visibility === 'private') {
        const message = prompt('Nachricht an den Admin (optional):');
        if (message === null) return;
        await createJoinRequest(groupId, userId, message);
    } else {
        await addMemberToGroup(groupId, userId);
    }
}

// ===========================
// SUCHE
// ===========================

function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    let searchTimeout;

    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(async () => {
            const term = e.target.value.trim();
            // ✅ Lokal filtern statt neuen API Call
            if (term === '') {
                filteredGroups = [...allGroups];
            } else {
                filteredGroups = allGroups.filter(g =>
                    (g.title || '').toLowerCase().includes(term.toLowerCase()) ||
                    (g.subject || '').toLowerCase().includes(term.toLowerCase()) ||
                    (g.topic || '').toLowerCase().includes(term.toLowerCase()) ||
                    (g.description || '').toLowerCase().includes(term.toLowerCase())
                );
            }
            currentPage = 1;
            applyFilters();
        }, 300);
    });
}

// ===========================
// FILTER
// ===========================

function applyFilters() {
    filteredGroups = allGroups.filter(group => {
        const matchSubject = activeFilters.subjects.length === 0
            || activeFilters.subjects.includes(group.subject);
        const matchField = activeFilters.learningFields.length === 0
            || activeFilters.learningFields.includes(group.learningField || group.topic);

        const searchTerm = document.getElementById('searchInput')?.value.trim().toLowerCase() || '';
        const matchSearch = searchTerm === ''
            || (group.title || '').toLowerCase().includes(searchTerm)
            || (group.subject || '').toLowerCase().includes(searchTerm)
            || (group.topic || '').toLowerCase().includes(searchTerm)
            || (group.description || '').toLowerCase().includes(searchTerm);

        return matchSubject && matchField && matchSearch;
    });

    currentPage = 1;
    renderCurrentPage();
}

function updateFilterChips() {
    const container  = document.getElementById('filterChips');
    const badge      = document.getElementById('filterCountBadge');
    const allFilters = [...activeFilters.subjects, ...activeFilters.learningFields];
    container.innerHTML = '';

    if (allFilters.length > 0) {
        badge.textContent   = allFilters.length;
        badge.style.display = 'inline-block';
    } else {
        badge.style.display = 'none';
    }

    if (allFilters.length === 0) return;

    const toShow    = allFilters.slice(0, 2);
    const remaining = allFilters.length - 2;

    toShow.forEach(filter => {
        const chip = document.createElement('div');
        chip.className = 'filter-chip';
        chip.innerHTML = `${filter}<span class="filter-chip-remove" data-filter="${filter}">×</span>`;
        chip.querySelector('.filter-chip-remove').addEventListener('click', (e) => {
            e.stopPropagation();
            removeFilter(filter);
        });
        container.appendChild(chip);
    });

    if (remaining > 0) {
        const more = document.createElement('div');
        more.className   = 'filter-chip-more';
        more.textContent = `+${remaining}`;
        container.appendChild(more);
    }
}

function removeFilter(filterValue) {
    activeFilters.subjects       = activeFilters.subjects.filter(s => s !== filterValue);
    activeFilters.learningFields = activeFilters.learningFields.filter(f => f !== filterValue);

    const cb1 = document.querySelector(`.subject-filter[value="${filterValue}"]`);
    const cb2 = document.querySelector(`.learning-field-filter[value="${filterValue}"]`);
    if (cb1) cb1.checked = false;
    if (cb2) cb2.checked = false;

    updateFilterChips();
    applyFilters();
}

function setupFilter() {
    const filterBtn      = document.getElementById('filterBtn');
    const filterDropdown = document.getElementById('filterDropdown');
    const resetFilter    = document.getElementById('resetFilter');
    const applyFilter    = document.getElementById('applyFilter');

    filterBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        filterDropdown.classList.toggle('active');
    });

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.filter-dropdown') && !e.target.closest('.filter-btn')) {
            filterDropdown.classList.remove('active');
        }
    });

    document.querySelectorAll('.subject-filter').forEach(cb => {
        cb.addEventListener('change', (e) => {
            if (e.target.checked) activeFilters.subjects.push(e.target.value);
            else activeFilters.subjects = activeFilters.subjects.filter(s => s !== e.target.value);
            updateFilterChips();
        });
    });

    document.querySelectorAll('.learning-field-filter').forEach(cb => {
        cb.addEventListener('change', (e) => {
            if (e.target.checked) activeFilters.learningFields.push(e.target.value);
            else activeFilters.learningFields = activeFilters.learningFields.filter(f => f !== e.target.value);
            updateFilterChips();
        });
    });

    applyFilter.addEventListener('click', () => {
        applyFilters();
        filterDropdown.classList.remove('active');
    });

    resetFilter.addEventListener('click', () => {
        activeFilters.subjects       = [];
        activeFilters.learningFields = [];
        document.querySelectorAll('.subject-filter, .learning-field-filter')
            .forEach(cb => cb.checked = false);
        updateFilterChips();
        filteredGroups = [...allGroups];
        currentPage    = 1;
        renderCurrentPage();
        filterDropdown.classList.remove('active');
    });
}

// ===========================
// MODAL (Gruppe erstellen)
// ===========================

function setupModal() {
    const modal    = document.getElementById('groupModal');
    const openBtn  = document.getElementById('addGroupBtn');
    const closeBtn = document.getElementById('closeModal');
    const form     = document.getElementById('groupForm');

    openBtn.addEventListener('click', () => modal.style.display = 'block');

    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
        form.reset();
    });

    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
            form.reset();
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.disabled    = true;
        submitBtn.textContent = 'Wird erstellt...';

        const groupData = {
            name:          document.getElementById('groupName').value.trim(),
            subject:       document.getElementById('subject').value,
            learningField: document.getElementById('learningField').value,
            description:   document.getElementById('groupDetails').value.trim() || null,
            type:          document.getElementById('groupType')?.value            || 'online',
            location:      document.getElementById('groupLocation')?.value.trim() || null,
            className:     document.getElementById('groupClass')?.value.trim()    || null,
            maxUsers:      document.getElementById('groupMaxUsers')?.value        || null,
        };

        if (!groupData.name) {
            showMessage('Bitte gib einen Gruppennamen ein', 'error');
            submitBtn.disabled    = false;
            submitBtn.textContent = 'Gruppe erstellen';
            return;
        }

        const result = await createGroup(groupData);

        submitBtn.disabled    = false;
        submitBtn.textContent = 'Gruppe erstellen';

        if (result) {
            form.reset();
            modal.style.display = 'none';
        }
    });
}

// ===========================
// AVATAR DROPDOWN
// ===========================

function setupAvatarDropdown() {
    const avatar   = document.getElementById('userAvatar');
    const dropdown = document.getElementById('avatarDropdown');
    const role     = localStorage.getItem('role') || 'user';

    document.getElementById('avatarDropdownName').textContent  = localStorage.getItem('displayName') || 'Benutzer';
    document.getElementById('avatarDropdownEmail').textContent = localStorage.getItem('email') || '';

    if (role === 'admin' || role === 'teacher') {
        const adminBtn = document.createElement('button');
        adminBtn.className = 'avatar-dropdown-item';
        adminBtn.innerHTML = `<i class="pi pi-shield"></i><span>Adminbereich</span>`;
        adminBtn.addEventListener('click', () => window.location.href = 'admin.html');
        const logoutBtn = document.getElementById('logoutBtn');
        logoutBtn.parentNode.insertBefore(adminBtn, logoutBtn);
    }

    avatar.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('open');
    });

    document.addEventListener('click', (e) => {
        if (!avatar.contains(e.target)) dropdown.classList.remove('open');
    });

    document.getElementById('logoutBtn').addEventListener('click', handleLogout);
    document.getElementById('deleteAccountBtn').addEventListener('click', () => {
        dropdown.classList.remove('open');
        showDeleteAccountConfirm();
    });
}

// ===========================
// LOGOUT
// ===========================

function handleLogout() {
    localStorage.clear();
    showMessage('Du wurdest abgemeldet. Weiterleitung...', 'success');
    setTimeout(() => window.location.href = 'login.html', 1000);
}

// ===========================
// KONTO LÖSCHEN
// ===========================

function showDeleteAccountConfirm() {
    const existing = document.querySelector('.confirm-modal-overlay');
    if (existing) existing.remove();

    const overlay = document.createElement('div');
    overlay.className = 'confirm-modal-overlay';
    overlay.innerHTML = `
        <div class="confirm-modal">
            <h3><i class="pi pi-exclamation-triangle"></i> Konto löschen</h3>
            <p>
                Bist du sicher, dass du dein Konto dauerhaft löschen möchtest?<br>
                <strong>Diese Aktion kann nicht rückgängig gemacht werden.</strong>
            </p>
            <div class="confirm-modal-buttons">
                <button class="confirm-btn-cancel" id="cancelDeleteBtn">Abbrechen</button>
                <button class="confirm-btn-delete" id="confirmDeleteBtn">
                    <i class="pi pi-trash"></i> Ja, löschen
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);

    document.getElementById('cancelDeleteBtn').addEventListener('click', () => overlay.remove());
    document.getElementById('confirmDeleteBtn').addEventListener('click', async () => {
        await handleDeleteAccount();
        overlay.remove();
    });

    const handleKey = (e) => {
        if (e.key === 'Escape') {
            overlay.remove();
            document.removeEventListener('keydown', handleKey);
        }
    };
    document.addEventListener('keydown', handleKey);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.remove(); });
}

async function handleDeleteAccount() {
    const userId = localStorage.getItem('userId');
    if (!userId) { showMessage('Benutzer nicht gefunden', 'error'); return; }

    try {
        const response = await fetch(`${API_BASE_URL}/api/users/${userId}`, {
            method:  'DELETE',
            headers: getHeaders(true)
        });
        if (!response.ok) throw new Error(`Fehler beim Löschen: ${response.status}`);
        showMessage('Konto wurde gelöscht. Weiterleitung...', 'success');
        localStorage.clear();
        setTimeout(() => window.location.href = 'login.html', 1500);
    } catch (error) {
        console.error('Fehler beim Löschen:', error);
        showMessage('Konto konnte nicht gelöscht werden', 'error');
    }
}

// ===========================
// USER INFO
// ===========================

async function loadUserInfo() {
    if (!isLoggedIn()) {
        window.location.href = 'login.html';
        return;
    }

    const displayName = localStorage.getItem('displayName');
    const email       = localStorage.getItem('email');
    const label       = document.getElementById('userNameLabel');

    if (displayName)   label.textContent = displayName;
    else if (email)    label.textContent = email.split('@')[0];
    else               label.textContent = 'Gast';
}

// ===========================
// INIT
// ===========================

document.addEventListener('DOMContentLoaded', async () => {
    await loadUserInfo();

    await Promise.all([
        fetchGroups(),
        fetchMyGroups()
    ]);

    applyFilters();
    setupPagination();
    setupSearch();
    setupFilter();
    setupModal();
    setupAvatarDropdown();
});

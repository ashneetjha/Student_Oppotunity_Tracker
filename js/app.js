/**
 * OpportunityHub — Central API Client and Frontend Controller
 * Connects all UI views directly to the FastAPI Backend.
 */

const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'https://student-opportunity-tracker-api.onrender.com/api'
  : '/api';

// --- AUTH & STATE HELPERS ---
function getToken() {
  return localStorage.getItem('access_token');
}

function setToken(token) {
  if (token) localStorage.setItem('access_token', token);
  else localStorage.removeItem('access_token');
}

function getCurrentUser() {
  const userStr = localStorage.getItem('currentUser');
  try {
    return userStr ? JSON.parse(userStr) : null;
  } catch (e) {
    return null;
  }
}

function setCurrentUser(user) {
  if (user) localStorage.setItem('currentUser', JSON.stringify(user));
  else localStorage.removeItem('currentUser');
}

function authHeaders() {
  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  options.headers = { ...authHeaders(), ...(options.headers || {}) };
  
  try {
    const response = await fetch(url, options);
    if (response.status === 401) {
      // Token expired or invalid
      console.warn('Session expired or unauthorized. Redirecting to login.');
      // Avoid looping if already on login/register/index
      const path = location.pathname;
      if (!path.includes('login.html') && !path.includes('register.html') && !path.includes('index.html') && path !== '/') {
        setToken(null);
        setCurrentUser(null);
        location.href = 'login.html';
      }
    }
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      const errorMsg = data && (data.detail || data.message) ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)) : `Request failed with status ${response.status}`;
      throw new Error(errorMsg);
    }
    return data;
  } catch (err) {
    console.error(`API Error [${endpoint}]:`, err);
    throw err;
  }
}

// In-memory cache for fast search & filtering in explore view
let cachedOpportunities = [];
let cachedUserBookmarks = new Set();
let cachedUserApplications = {};

// Sync topbar user profile & sidebar active link across all pages
function syncUIHeader() {
  const user = getCurrentUser();
  if (user) {
    document.querySelectorAll('.user-mini').forEach(el => {
      const nameEl = el.querySelector('b');
      const roleEl = el.querySelector('small');
      const avatarEl = el.querySelector('.avatar');
      if (nameEl) nameEl.textContent = user.name;
      if (roleEl) roleEl.textContent = user.role === 'admin' ? 'Administrator' : 'Student';
      if (avatarEl) avatarEl.textContent = (user.name || 'U')[0].toUpperCase();
    });
  }

  // Logout button binding
  document.querySelectorAll('.logout').forEach(el => {
    el.onclick = (e) => {
      e.preventDefault();
      logoutUser();
    };
  });

  // Highlight current sidebar item
  const currentFile = location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-item').forEach(el => {
    const href = el.getAttribute('href');
    if (href === currentFile) {
      el.classList.add('active');
    } else {
      el.classList.remove('active');
    }
  });

  // Admin link visibility check
  const adminNav = document.querySelector('a[href="admin.html"]');
  if (adminNav && user && user.role !== 'admin') {
    // Keep it clickable or styled appropriately for demo
  }
}

function logoutUser() {
  setToken(null);
  setCurrentUser(null);
  location.href = 'login.html';
}

function togglePassword() {
  const p = document.getElementById("password") || document.getElementById("regPassword");
  if (p) p.type = p.type === "password" ? "text" : "password";
}

function globalSearch(v) {
  if (v.trim().length > 1 && !location.pathname.endsWith("explore.html")) {
    location.href = "explore.html?search=" + encodeURIComponent(v);
  } else if (location.pathname.endsWith("explore.html")) {
    const input = document.getElementById("oppSearch");
    if (input) {
      input.value = v;
      filterOpps();
    }
  }
}

// --- AUTHENTICATION FLOWS ---
async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById("email")?.value;
  const password = document.getElementById("password")?.value;
  const btn = e.target.querySelector('button[type="submit"]');
  const originalText = btn ? btn.textContent : 'Sign In';

  try {
    if (btn) btn.textContent = 'Signing in...';
    const res = await apiFetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });

    setToken(res.access_token);
    setCurrentUser(res.user);

    if (res.user.role === 'admin') {
      location.href = 'admin.html';
    } else {
      location.href = 'dashboard.html';
    }
  } catch (err) {
    alert("Login failed: " + err.message);
  } finally {
    if (btn) btn.textContent = originalText;
  }
}

async function registerUser(e) {
  e.preventDefault();
  const firstName = document.getElementById("regFirstName")?.value || "";
  const lastName = document.getElementById("regLastName")?.value || "";
  const name = `${firstName} ${lastName}`.trim();
  const email = document.getElementById("regEmail")?.value;
  const college = document.getElementById("regCollege")?.value;
  const password = document.getElementById("regPassword")?.value;

  try {
    const res = await apiFetch('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, college, password, role: 'student' })
    });

    setToken(res.access_token);
    setCurrentUser(res.user);
    alert("Account created successfully!");
    location.href = "dashboard.html";
  } catch (err) {
    alert("Registration failed: " + err.message);
  }
}

// --- BOOKMARK FLOWS ---
async function toggleBookmark(id) {
  const token = getToken();
  if (!token) {
    alert("Please log in to bookmark opportunities.");
    location.href = "login.html";
    return;
  }

  try {
    const res = await apiFetch(`/bookmarks/${id}/toggle`, { method: 'POST' });
    if (res.is_bookmarked) {
      cachedUserBookmarks.add(id);
    } else {
      cachedUserBookmarks.delete(id);
    }

    // Refresh active views
    updateCounts();
    if (document.getElementById("bookmarkGrid")) renderBookmarks();
    if (document.getElementById("opportunityGrid")) filterOpps();
    if (document.getElementById("recommended")) loadDashboardRecommended();
    if (document.getElementById("opportunityDetail")) renderDetail();
  } catch (err) {
    alert("Error updating bookmark: " + err.message);
  }
}

function isSaved(id) {
  return cachedUserBookmarks.has(Number(id));
}

async function updateCounts() {
  const token = getToken();
  if (!token) return;

  try {
    const bookmarks = await apiFetch('/bookmarks');
    cachedUserBookmarks = new Set(bookmarks.map(b => b.opportunity_id || b.id));
    const count = cachedUserBookmarks.size;
    
    document.querySelectorAll("#bookmarkCount").forEach(e => e.textContent = count);
    const s = document.getElementById("savedStat");
    if (s) s.textContent = count;
  } catch (err) {
    // Non-blocking
  }
}

function daysLabel(o) {
  return `${o.days} days left`;
}

function card(o) {
  const saved = isSaved(o.id || o.opportunity_id);
  const formattedDate = o.deadline ? new Date(o.deadline).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }) : "N/A";
  const skillsList = Array.isArray(o.skills) ? o.skills : [];

  return `<article class="opp-card">
  <div class="card-top">
    <span class="type-badge">${o.type}</span>
    <button class="save-btn ${saved ? "saved" : ""}" onclick="toggleBookmark(${o.id || o.opportunity_id})">${saved ? "♥" : "♡"}</button>
  </div>
  <h3>${o.title}</h3>
  <div class="company">${o.org || o.organization} · ${o.location}</div>
  <p class="opp-description">${o.desc || o.description}</p>
  <div class="card-meta">${skillsList.map(s => `<span class="skill-chip">${s}</span>`).join("")}</div>
  <div class="card-bottom">
    <div class="deadline">Deadline<strong>${formattedDate}</strong></div>
    <a class="card-link" href="opportunity.html?id=${o.id || o.opportunity_id}">View Details →</a>
  </div>
  </article>`;
}

// --- EXPLORE & OPPORTUNITY LISTING ---
async function fetchAndRenderOpportunities() {
  try {
    const opps = await apiFetch('/opportunities');
    cachedOpportunities = opps;
    filterOpps();
  } catch (err) {
    const el = document.getElementById("opportunityGrid");
    if (el) {
      el.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><div>⚠️</div><h2>Unable to load opportunities</h2><p>${err.message}</p></div>`;
    }
  }
}

function filterOpps() {
  const q = (document.getElementById("oppSearch")?.value || "").toLowerCase().trim();
  const type = document.getElementById("typeFilter")?.value || "";
  const skill = document.getElementById("skillFilter")?.value || "";
  const d = parseInt(document.getElementById("deadlineFilter")?.value || "0");

  const list = cachedOpportunities.filter(o => {
    const titleMatch = (o.title || "").toLowerCase();
    const orgMatch = (o.org || o.organization || "").toLowerCase();
    const skillsList = Array.isArray(o.skills) ? o.skills : [];
    const skillsMatch = skillsList.join(" ").toLowerCase();
    const descMatch = (o.desc || o.description || "").toLowerCase();
    const textMatches = !q || (titleMatch + " " + orgMatch + " " + skillsMatch + " " + descMatch).includes(q);

    const typeMatches = !type || o.type === type;
    const skillMatches = !skill || skillsList.some(s => s.toLowerCase() === skill.toLowerCase());
    const deadlineMatches = !d || o.days <= d;

    return textMatches && typeMatches && skillMatches && deadlineMatches;
  });

  const el = document.getElementById("opportunityGrid");
  if (el) {
    el.innerHTML = list.length
      ? list.map(card).join("")
      : `<div class="empty-state" style="grid-column:1/-1"><div>⌕</div><h2>No opportunities found</h2><p>Try changing your filters or search.</p></div>`;
  }
  const c = document.getElementById("resultCount");
  if (c) c.textContent = `${list.length} opportunities`;
}

// --- BOOKMARKS PAGE ---
async function renderBookmarks() {
  const el = document.getElementById("bookmarkGrid");
  const empty = document.getElementById("emptyBookmarks");
  if (!el) return;

  try {
    const list = await apiFetch('/bookmarks');
    cachedUserBookmarks = new Set(list.map(b => b.opportunity_id || b.id));
    el.innerHTML = list.length ? list.map(card).join("") : "";
    if (empty) empty.style.display = list.length ? "none" : "block";
    updateCounts();
  } catch (err) {
    el.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><p>${err.message}</p></div>`;
  }
}

// --- DEADLINE TRACKER PAGE ---
async function renderAllDeadlines() {
  const el = document.getElementById("allDeadlines");
  if (!el) return;

  try {
    const list = await apiFetch('/opportunities?sort=deadline_asc');
    el.innerHTML = list.map(o => {
      const formattedDate = o.deadline ? new Date(o.deadline).toLocaleDateString("en-IN", { weekday: "short", day: "2-digit", month: "short" }) : "N/A";
      return `<div class="deadline-item ${o.days <= 7 ? "urgent" : ""}">
        <div class="date">${formattedDate}</div>
        <b>${o.title}</b>
        <small>${o.org || o.organization} · ${o.days} days left</small>
        <span class="type-badge">${o.type}</span>
      </div>`;
    }).join("");

    // Update deadline summary KPI cards
    const upcomingCount = list.filter(o => o.days <= 30).length;
    const weekCount = list.filter(o => o.days <= 7).length;
    const monthCount = list.filter(o => o.days <= 30).length;
    const urgentCount = list.filter(o => o.days <= 3).length;

    const upEl = document.getElementById("deadlineUpcomingCount");
    if (upEl) upEl.textContent = upcomingCount;
    const wkEl = document.getElementById("deadlineWeekCount");
    if (wkEl) wkEl.textContent = weekCount;
    const moEl = document.getElementById("deadlineMonthCount");
    if (moEl) moEl.textContent = monthCount;
    const urgEl = document.getElementById("deadlineUrgentCount");
    if (urgEl) urgEl.textContent = weekCount; // matching <= 7 days
  } catch (err) {
    el.innerHTML = `<p style="padding:20px; color:#e05e5e">Error loading deadlines: ${err.message}</p>`;
  }
}

// --- APPLICATIONS TRACKER PAGE ---
let currentAppTab = 'All';
async function renderApplications(tab = 'All') {
  currentAppTab = tab;
  const el = document.getElementById("applicationTable");
  if (!el) return;

  try {
    const apps = await apiFetch('/applications');
    
    // Update tab counts
    const countAll = apps.length;
    const countInt = apps.filter(a => a.status === 'Interested').length;
    const countApp = apps.filter(a => a.status === 'Applied').length;
    const countShort = apps.filter(a => a.status === 'Shortlisted').length;
    const countComp = apps.filter(a => a.status === 'Completed').length;

    const tAll = document.getElementById("tabCountAll"); if (tAll) tAll.textContent = countAll;
    const tInt = document.getElementById("tabCountInterested"); if (tInt) tInt.textContent = countInt;
    const tApp = document.getElementById("tabCountApplied"); if (tApp) tApp.textContent = countApp;
    const tShort = document.getElementById("tabCountShortlisted"); if (tShort) tShort.textContent = countShort;
    const tComp = document.getElementById("tabCountCompleted"); if (tComp) tComp.textContent = countComp;

    const filtered = apps.filter(a => tab === 'All' || a.status === tab);

    if (filtered.length === 0) {
      el.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:40px; color:#888;">No applications found in this tab.</td></tr>`;
      return;
    }

    el.innerHTML = filtered.map(a => {
      const o = a.opportunity || {};
      const appliedDate = a.applied_at ? new Date(a.applied_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short" }) : "—";
      const deadlineDate = o.deadline ? new Date(o.deadline).toLocaleDateString("en-IN", { day: "2-digit", month: "short" }) : "—";
      const logo = o.logo || (o.organization ? o.organization[0].toUpperCase() : "O");
      const title = o.title || "Opportunity";
      const org = o.organization || o.org || "";
      const type = o.type || "Internship";

      return `<tr>
        <td>
          <div class="table-opp">
            <span class="table-logo">${logo}</span>
            <div><b>${title}</b><small class="company">${org}</small></div>
          </div>
        </td>
        <td>${type}</td>
        <td>${a.status === "Interested" ? "—" : appliedDate}</td>
        <td><span class="status-badge ${a.status.toLowerCase()}">${a.status}</span></td>
        <td>${deadlineDate}</td>
        <td><a class="action-link" href="opportunity.html?id=${a.opportunity_id}">View</a></td>
      </tr>`;
    }).join("");
  } catch (err) {
    el.innerHTML = `<tr><td colspan="6" style="color:#e05e5e; padding:20px;">Error loading applications: ${err.message}</td></tr>`;
  }
}

function setAppTab(tab, btn) {
  document.querySelectorAll(".tab").forEach(x => x.classList.remove("active"));
  if (btn) btn.classList.add("active");
  renderApplications(tab);
}

// --- STUDENT DASHBOARD PAGE ---
async function renderDashboard() {
  const user = getCurrentUser();
  if (user) {
    const greetingEl = document.getElementById("dashGreeting");
    if (greetingEl) greetingEl.textContent = `Good day, ${user.name.split(" ")[0]} 👋`;
  }

  const dateEl = document.getElementById("dashDate");
  if (dateEl) {
    dateEl.textContent = new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" });
  }

  try {
    const data = await apiFetch('/dashboard/student');
    const { stats, upcoming_deadlines, recommended } = data;

    // Update KPI stat counters
    const savedEl = document.getElementById("savedStat"); if (savedEl) savedEl.textContent = stats.bookmarks;
    const appEl = document.getElementById("dashAppStat"); if (appEl) appEl.textContent = stats.applications;
    const shortEl = document.getElementById("dashShortlistedStat"); if (shortEl) shortEl.textContent = stats.shortlisted;
    const ddlEl = document.getElementById("dashDeadlinesStat"); if (ddlEl) ddlEl.textContent = stats.upcoming_deadlines_count;

    // Progress chart numbers
    const centerEl = document.getElementById("donutCenter");
    if (centerEl) centerEl.innerHTML = `<b>${stats.applications}</b><span>Applications</span>`;

    const intEl = document.getElementById("legendInterested"); if (intEl) intEl.textContent = stats.interested;
    const apEl = document.getElementById("legendApplied"); if (apEl) apEl.textContent = stats.applied;
    const shEl = document.getElementById("legendShortlisted"); if (shEl) shEl.textContent = stats.shortlisted;
    const coEl = document.getElementById("legendCompleted"); if (coEl) coEl.textContent = stats.completed;

    // Recommended list
    const recEl = document.getElementById("recommended");
    if (recEl) {
      recEl.innerHTML = recommended.map(o => `
        <div class="opp-row">
          <div class="opp-info">
            <span class="opp-logo">${o.logo}</span>
            <div><b>${o.title}</b><small>${o.org || o.organization} · ${o.location}</small></div>
          </div>
          <div class="right">
            <span class="type-badge">${o.type}</span>
            <small>${o.days} days left</small>
          </div>
        </div>
      `).join("");
    }

    // Dashboard upcoming deadlines (horizontal 4-grid)
    const ddlListEl = document.getElementById("dashDeadlines");
    if (ddlListEl) {
      ddlListEl.innerHTML = upcoming_deadlines.map(o => {
        const formattedDate = o.deadline ? new Date(o.deadline).toLocaleDateString("en-IN", { weekday: "short", day: "2-digit", month: "short" }) : "N/A";
        return `<div class="deadline-item ${o.days <= 7 ? "urgent" : ""}">
          <div class="date">${formattedDate}</div>
          <b>${o.title}</b>
          <small>${o.org || o.organization} · ${o.days} days left</small>
          <span class="type-badge">${o.type}</span>
        </div>`;
      }).join("");
    }

    updateCounts();
  } catch (err) {
    console.error("Dashboard error:", err);
  }
}

// --- OPPORTUNITY DETAIL PAGE ---
let currentDetailOpp = null;
async function renderDetail() {
  const params = new URLSearchParams(location.search);
  const id = parseInt(params.get("id") || "1");
  const el = document.getElementById("opportunityDetail");
  if (!el) return;

  try {
    const opp = await apiFetch(`/opportunities/${id}`);
    currentDetailOpp = opp;

    const formattedDeadline = opp.deadline ? new Date(opp.deadline).toLocaleDateString("en-IN", { day: "2-digit", month: "long", year: "numeric" }) : "N/A";
    const saved = isSaved(opp.id || opp.opportunity_id);
    const appStatusText = opp.application_status;
    const actionBtnText = appStatusText ? (appStatusText === "Interested" ? "Apply Now →" : `Status: ${appStatusText} (Click to Advance)`) : "Apply Now →";

    el.innerHTML = `
      <a href="explore.html" class="detail-back">← Back to opportunities</a>
      <section class="detail-hero">
        <div class="detail-title">
          <div class="detail-logo">${opp.logo}</div>
          <div>
            <span class="type-badge">${opp.type}</span>
            <h1>${opp.title}</h1>
            <p>${opp.org || opp.organization} · ${opp.location}</p>
          </div>
        </div>
        <div class="detail-actions">
          <button class="btn btn-light" onclick="toggleBookmark(${opp.id || opp.opportunity_id})">${saved ? "♥ Saved" : "♡ Save"}</button>
          <button class="btn btn-primary" onclick="advanceApplication(${opp.id || opp.opportunity_id})">${actionBtnText}</button>
        </div>
      </section>
      <div class="detail-grid">
        <section class="panel">
          <h2>About this opportunity</h2>
          <p>${opp.desc || opp.description} This opportunity is designed to help students gain practical experience, strengthen their portfolio and connect with industry professionals.</p>
          <h2>Eligibility & Overview</h2>
          <p>${opp.eligibility || "Open to all enrolled undergraduate students in relevant programs."}</p>
          <h2>Skills required</h2>
          <div class="chips">${(opp.skills || []).map(s => `<span class="selected">${s}</span>`).join("")}</div>
        </section>
        <aside class="panel detail-sidebar">
          <h2>Opportunity details</h2>
          <div class="info-row"><span>Organization</span><b>${opp.org || opp.organization}</b></div>
          <div class="info-row"><span>Type</span><b>${opp.type}</b></div>
          <div class="info-row"><span>Location</span><b>${opp.location}</b></div>
          <div class="info-row"><span>Deadline</span><b>${formattedDeadline}</b></div>
          <div class="info-row"><span>Time remaining</span><b class="danger-text">${daysLabel(opp)}</b></div>
          <div class="info-row"><span>Current Status</span><b style="color:#635bff">${opp.application_status || "Not yet applied"}</b></div>
          <button class="btn btn-primary full" style="margin-top:15px;" onclick="advanceApplication(${opp.id || opp.opportunity_id})">Apply for this opportunity</button>
        </aside>
      </div>
    `;
  } catch (err) {
    el.innerHTML = `<div class="empty-state"><h2>Opportunity not found</h2><p>${err.message}</p><a href="explore.html" class="btn btn-primary">Back to Explore</a></div>`;
  }
}

async function advanceApplication(oppId) {
  const token = getToken();
  if (!token) {
    alert("Please log in to apply for opportunities.");
    location.href = "login.html";
    return;
  }

  const current = currentDetailOpp ? currentDetailOpp.application_status : null;
  let nextStatus = "Applied";
  if (!current || current === "Interested") {
    nextStatus = "Applied";
  } else if (current === "Applied") {
    nextStatus = "Shortlisted";
  } else if (current === "Shortlisted") {
    nextStatus = "Completed";
  } else {
    nextStatus = "Applied";
  }

  try {
    await apiFetch(`/applications/${oppId}`, {
      method: 'POST',
      body: JSON.stringify({ status: nextStatus })
    });
    alert(`Application status successfully updated to "${nextStatus}"!`);
    renderDetail();
  } catch (err) {
    alert("Error updating application: " + err.message);
  }
}

// --- ADMIN PORTAL FLOWS ---
let cachedAdminOpps = [];
async function renderAdmin() {
  const el = document.getElementById("adminTable");
  if (!el) return;

  try {
    // Load admin dashboard statistics
    const dashData = await apiFetch('/dashboard/admin');
    const { stats, recent_opportunities } = dashData;

    const totEl = document.getElementById("adminStatTotal"); if (totEl) totEl.textContent = stats.total_opportunities;
    const actEl = document.getElementById("adminStatActive"); if (actEl) actEl.textContent = stats.active_opportunities;
    const stuEl = document.getElementById("adminStatStudents"); if (stuEl) stuEl.textContent = stats.total_students;
    const appEl = document.getElementById("adminStatApps"); if (appEl) appEl.textContent = stats.total_applications;

    // Load full opportunities list for management
    const opps = await apiFetch('/opportunities');
    cachedAdminOpps = opps;
    populateAdminTable(opps);
  } catch (err) {
    console.error("Admin portal error:", err);
    if (el) el.innerHTML = `<tr><td colspan="6" style="padding:20px; color:#e05e5e">Error loading admin data: ${err.message}</td></tr>`;
  }
}

function populateAdminTable(list) {
  const el = document.getElementById("adminTable");
  if (!el) return;

  if (list.length === 0) {
    el.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:30px; color:#888;">No opportunities found.</td></tr>`;
    return;
  }

  el.innerHTML = list.map(o => {
    const formattedDate = o.deadline ? new Date(o.deadline).toLocaleDateString("en-IN", { day: "2-digit", month: "short" }) : "—";
    return `<tr>
      <td>
        <div class="table-opp">
          <span class="table-logo">${o.logo}</span>
          <b>${o.title}</b>
        </div>
      </td>
      <td>${o.org || o.organization}</td>
      <td>${o.type}</td>
      <td>${formattedDate}</td>
      <td><span class="status-badge ${o.status.toLowerCase() === 'active' ? 'shortlisted' : 'completed'}">${o.status}</span></td>
      <td>
        <a class="action-link" href="opportunity.html?id=${o.id || o.opportunity_id}">View</a> · 
        <a class="action-link" href="javascript:void(0)" onclick="openEditModal(${o.id || o.opportunity_id})">Edit</a> · 
        <a class="action-link" href="javascript:void(0)" style="color:#e05e5e;" onclick="deleteOpportunityById(${o.id || o.opportunity_id})">Delete</a>
      </td>
    </tr>`;
  }).join("");
}

function filterAdminTable(term) {
  const q = term.toLowerCase().trim();
  const filtered = cachedAdminOpps.filter(o => 
    (o.title + " " + (o.org || o.organization) + " " + o.type).toLowerCase().includes(q)
  );
  populateAdminTable(filtered);
}

function openModal() {
  document.getElementById("editOppId").value = "";
  document.getElementById("modalTitle").textContent = "Add Opportunity";
  document.getElementById("modalSubmitBtn").textContent = "Publish Opportunity";
  document.getElementById("newTitle").value = "";
  document.getElementById("newOrg").value = "";
  document.getElementById("newType").value = "Internship";
  document.getElementById("newDeadline").value = "";
  document.getElementById("newSkills").value = "";
  document.getElementById("modal")?.classList.add("show");
}

function closeModal() {
  document.getElementById("modal")?.classList.remove("show");
}

function openEditModal(id) {
  const opp = cachedAdminOpps.find(o => (o.id || o.opportunity_id) === id);
  if (!opp) return;

  document.getElementById("editOppId").value = id;
  document.getElementById("modalTitle").textContent = "Edit Opportunity";
  document.getElementById("modalSubmitBtn").textContent = "Update Opportunity";
  document.getElementById("newTitle").value = opp.title || "";
  document.getElementById("newOrg").value = opp.org || opp.organization || "";
  document.getElementById("newType").value = opp.type || "Internship";
  document.getElementById("newDeadline").value = opp.deadline ? opp.deadline.split("T")[0] : "";
  document.getElementById("newSkills").value = Array.isArray(opp.skills) ? opp.skills.join(", ") : "";
  document.getElementById("modal")?.classList.add("show");
}

async function saveOpportunityForm(e) {
  e.preventDefault();
  const editId = document.getElementById("editOppId").value;
  const title = document.getElementById("newTitle").value.trim();
  const organization = document.getElementById("newOrg").value.trim();
  const type = document.getElementById("newType").value;
  const deadline = document.getElementById("newDeadline").value;
  const skills = document.getElementById("newSkills").value
    .split(",")
    .map(s => s.trim())
    .filter(Boolean);

  const payload = {
    title,
    organization,
    type,
    deadline,
    description: `Official ${type} opportunity at ${organization}. Connect with professionals and grow your skills.`,
    location: "Online",
    eligibility: "Open to all verified college students",
    status: "Active",
    skills
  };

  try {
    if (editId) {
      await apiFetch(`/opportunities/${editId}`, {
        method: 'PUT',
        body: JSON.stringify(payload)
      });
      alert("Opportunity updated successfully!");
    } else {
      await apiFetch('/opportunities', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      alert("Opportunity published successfully!");
    }

    closeModal();
    renderAdmin();
  } catch (err) {
    alert("Operation failed: " + err.message);
  }
}

async function deleteOpportunityById(id) {
  if (!confirm("Are you sure you want to permanently delete this opportunity?")) return;

  try {
    await apiFetch(`/opportunities/${id}`, { method: 'DELETE' });
    alert("Opportunity deleted successfully!");
    renderAdmin();
  } catch (err) {
    alert("Delete failed: " + err.message);
  }
}

// --- PROFILE PAGE FLOWS ---
async function loadUserProfile() {
  const elName = document.getElementById("profileCardName");
  if (!elName) return;

  try {
    const user = await apiFetch('/auth/me');
    setCurrentUser(user);

    document.getElementById("profileCardName").textContent = user.name;
    document.getElementById("profileCardEmail").textContent = user.email;
    document.getElementById("profileCardRole").textContent = user.role === 'admin' ? 'Administrator' : 'Student';
    document.getElementById("profileBigAvatar").textContent = user.name[0].toUpperCase();

    const parts = user.name.split(" ");
    document.getElementById("profileFirstName").value = parts[0] || "";
    document.getElementById("profileLastName").value = parts.slice(1).join(" ") || "";
    document.getElementById("profileEmail").value = user.email;
    document.getElementById("profileCollege").value = user.college || "";
    if (user.bio) document.getElementById("profileBio").value = user.bio;
  } catch (err) {
    console.error("Profile load error:", err);
  }
}

async function saveProfile() {
  const firstName = document.getElementById("profileFirstName")?.value || "";
  const lastName = document.getElementById("profileLastName")?.value || "";
  const name = `${firstName} ${lastName}`.trim();
  const college = document.getElementById("profileCollege")?.value || "";
  const bio = document.getElementById("profileBio")?.value || "";

  try {
    const updated = await apiFetch('/auth/profile', {
      method: 'PUT',
      body: JSON.stringify({ name, college, bio })
    });
    setCurrentUser(updated);
    alert("Profile changes saved successfully to database!");
    loadUserProfile();
    syncUIHeader();
  } catch (err) {
    alert("Failed to save profile: " + err.message);
  }
}

// --- GLOBAL PAGE ROUTER & INIT ---
window.addEventListener("DOMContentLoaded", async () => {
  syncUIHeader();

  // Route protection for internal pages
  const publicPages = ['index.html', 'login.html', 'register.html', ''];
  const currentPage = location.pathname.split('/').pop() || 'index.html';
  const token = getToken();

  if (!token && !publicPages.includes(currentPage)) {
    // If opening page directly without logging in, provide easy demo prompt or redirect
    console.log("No token found, redirecting to login.html");
    location.href = 'login.html';
    return;
  }

  // Pre-load user bookmarks set if logged in
  if (token) {
    await updateCounts();
  }

  // Login form binding
  const loginForm = document.getElementById("loginForm");
  if (loginForm) loginForm.addEventListener("submit", handleLogin);

  // Explore page
  if (document.getElementById("opportunityGrid")) {
    await fetchAndRenderOpportunities();
    const q = new URLSearchParams(location.search).get("search");
    if (q && document.getElementById("oppSearch")) {
      document.getElementById("oppSearch").value = q;
      filterOpps();
    }
  }

  // Deadlines page
  if (document.getElementById("allDeadlines")) {
    renderAllDeadlines();
  }

  // Admin page
  if (document.getElementById("adminTable")) {
    renderAdmin();
  }

  // Profile page
  if (document.getElementById("profileCardName")) {
    loadUserProfile();
  }
});

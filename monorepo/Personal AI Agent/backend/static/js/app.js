// Global variables
let token = localStorage.getItem('token');
const API_URL = window.location.origin + '/api';

// Debug message - VERSION CHECK
console.log("🚀 App.js loaded successfully! [VERSION 3.0 - CACHE BUSTED]");
console.log("Using API URL:", API_URL);
console.log("🔧 This is the FIXED version with proper OAuth redirect");

// DOM elements
let loginSection, registerSection, appSection;

// Initialize DOM elements safely
function initDOMElements() {
    try {
        loginSection = document.getElementById('login-section');
        registerSection = document.getElementById('register-section');
        appSection = document.getElementById('app-section');

        console.log("DOM elements initialized:", { 
            loginSection: loginSection ? "found" : "missing", 
            registerSection: registerSection ? "found" : "missing", 
            appSection: appSection ? "found" : "missing" 
        });
        
        if (!loginSection || !registerSection || !appSection) {
            console.error("Some critical DOM elements are missing!");
        }
    } catch (error) {
        console.error("Error initializing DOM elements:", error);
    }
}

// Show the main container and hide loading indicator
function showMainContent() {
    const mainContainer = document.getElementById('main-container');
    const loadingIndicator = document.getElementById('loading');
    
    if (mainContainer) {
        mainContainer.style.display = 'block';
    }
    
    if (loadingIndicator) {
        loadingIndicator.style.display = 'none';
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM fully loaded");
    
    // Show main content
    showMainContent();
    
    // Initialize DOM elements
    initDOMElements();
    
    // Check for Gmail OAuth callback success
    const urlParams = new URLSearchParams(window.location.search);
    const gmailConnected = urlParams.get('gmail_connected');
    
    if (gmailConnected) {
        console.log("Gmail OAuth callback detected for email:", gmailConnected);
        // Clear the URL parameter to clean up the URL
        window.history.replaceState(null, null, window.location.pathname);
        
        // Show success message
        alert(`Gmail account ${gmailConnected} connected successfully! Please log in to access your emails.`);
    }
    
    // Check if user is logged in
    if (token) {
        console.log("User is logged in with token:", token);
        showAppSection();
        loadDocuments();
        loadSources();
        loadQueries();
        loadChatHistory(); // Load chat history on app load
    } else {
        console.log("No token found, showing login section");
        showLoginSection();
    }

    try {
    // Login form
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', handleLogin);
        } else {
            console.error("Login form not found!");
        }
    
    // Register form
        const registerForm = document.getElementById('register-form');
        if (registerForm) {
            registerForm.addEventListener('submit', handleRegister);
        } else {
            console.error("Register form not found!");
        }
    
    // Register button
        const registerBtn = document.getElementById('register-btn');
        if (registerBtn) {
            registerBtn.addEventListener('click', () => {
        loginSection.style.display = 'none';
        registerSection.style.display = 'block';
    });
        } else {
            console.error("Register button not found!");
        }
    
    // Back to login button
        const backToLoginBtn = document.getElementById('back-to-login');
        if (backToLoginBtn) {
            backToLoginBtn.addEventListener('click', () => {
        registerSection.style.display = 'none';
        loginSection.style.display = 'block';
    });
        } else {
            console.error("Back to login button not found!");
        }
    
    // Upload form
        const uploadForm = document.getElementById('upload-form');
        if (uploadForm) {
            uploadForm.addEventListener('submit', handleUpload);
        } else {
            console.error("Upload form not found!");
        }
    
    // Query form
        const queryForm = document.getElementById('query-form');
        if (queryForm) {
            queryForm.addEventListener('submit', handleQuery);
        } else {
            console.error("Query form not found!");
        }

        // Logout button
        const logoutBtn = document.getElementById('logout-btn');
        console.log("Looking for logout button...", logoutBtn);
        if (logoutBtn) {
            console.log("Logout button found, adding event listener");
            logoutBtn.addEventListener('click', async (event) => {
                console.log("🔴 LOGOUT BUTTON CLICKED - EVENT FIRED!", event);
                event.preventDefault();
                event.stopPropagation();
                
                try {
                    console.log("Calling backend logout endpoint...");
                    
                    // Call backend logout endpoint
                    const response = await fetch(`${API_URL}/logout`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                        }
                    });
                    
                    console.log("Backend logout response:", response);
                    const result = await response.json();
                    console.log("Backend logout result:", result);
                    
                    console.log("Backend logout successful");
                } catch (error) {
                    console.error("Error calling backend logout:", error);
                } finally {
                    // Always perform local logout regardless of backend response
                    console.log("Calling global logout function...");
                    logout();
                }
            });
            
            // Add a test click function to the button for debugging
            logoutBtn.setAttribute('data-debug', 'true');
            logoutBtn.title = 'Logout button - debug enabled';
            console.log("Logout button event listener added successfully");
        } else {
            console.error("❌ Logout button not found during initialization!");
        }
    } catch (error) {
        console.error("Error setting up event listeners:", error);
    }
});

// Auth functions
async function handleLogin(e) {
    e.preventDefault();
    
    try {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    console.log("Attempting login for user:", username);
    
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'username': username,
                'password': password
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error("Login failed with status:", response.status, errorData);
            throw new Error(`Login failed: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        token = data.access_token;
        localStorage.setItem('token', token);
        console.log("[DEBUG] Token received:", token);
        
        showAppSection();
        loadDocuments();
        loadSources();
        loadQueries();
    } catch (error) {
        console.error("Login error:", error);
        alert('Login failed: ' + error.message);
    }
}

// Patch fetch to log Authorization header for protected requests
const originalFetch = window.fetch;
window.fetch = async function(input, init) {
    if (init && init.headers && init.headers['Authorization']) {
        console.log('[DEBUG] Fetch Authorization header:', init.headers['Authorization']);
    }
    return originalFetch(input, init);
};

async function handleRegister(e) {
    e.preventDefault();
    
    const email = document.getElementById('reg-email').value;
    const username = document.getElementById('reg-username').value;
    const password = document.getElementById('reg-password').value;
    
    try {
        const response = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email,
                username,
                password
            })
        });
        
        if (!response.ok) {
            throw new Error('Registration failed');
        }
        
        alert('Registration successful! Please login.');
        registerSection.style.display = 'none';
        loginSection.style.display = 'block';
    } catch (error) {
        alert('Registration failed: ' + error.message);
    }
}

// Document functions
async function loadDocuments() {
    try {
        const response = await fetch(`${API_URL}/documents`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load documents');
        }
        
        const documents = await response.json();
        
        const documentsList = document.getElementById('documents-list');
        documentsList.innerHTML = '';
        
        if (documents.length === 0) {
            documentsList.innerHTML = '<p class="text-muted">No documents uploaded yet.</p>';
        } else {
            documents.forEach(doc => {
                // Get category badge info
                const categoryInfo = getCategoryInfo(doc.document_type || 'generic');
                
                // Add to documents list
                const item = document.createElement('a');
                item.href = '#';
                item.className = 'list-group-item list-group-item-action document-item';
                item.innerHTML = `
                    <div class="d-flex w-100 justify-content-between">
                        <h5 class="mb-1">
                            ${doc.title}
                            <span class="badge ${categoryInfo.badgeClass} ms-2">${categoryInfo.icon} ${categoryInfo.label}</span>
                        </h5>
                        <small>${new Date(doc.created_at).toLocaleDateString()}</small>
                    </div>
                    <p class="mb-1">${doc.description || 'No description'}</p>
                    <div class="d-flex justify-content-between align-items-center">
                        <small class="text-muted">
                            📄 PDF • ${formatFileSize(doc.file_size)} • ${categoryInfo.processingNote}
                        </small>
                        <button class="btn btn-sm btn-danger delete-doc" data-id="${doc.id}">Delete</button>
                    </div>
                `;
                documentsList.appendChild(item);
            });
            
            // Add event listeners to delete buttons
            document.querySelectorAll('.delete-doc').forEach(button => {
                button.addEventListener('click', async (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    if (confirm('Are you sure you want to delete this document?')) {
                        const docId = button.getAttribute('data-id');
                        await deleteDocument(docId);
                    }
                });
            });
        }
    } catch (error) {
        console.error('Error loading documents:', error);
    }
}

// Source functions
async function loadSources() {
    try {
        const response = await fetch(`${API_URL}/sources`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load sources');
        }
        
        const sources = await response.json();
        
        const sourceSelect = document.getElementById('source-select');
        // Clear and set default option
        sourceSelect.innerHTML = '<option value="">All Sources</option>';
        
        // Group sources by category
        const groupedSources = {
            all: [],
            documents: [],
            emails: []
        };
        
        sources.forEach(source => {
            groupedSources[source.source_category].push(source);
        });
        
        // Add All Sources (if not already there)
        if (groupedSources.all.length > 0) {
            // Skip - already added as default
        }
        
        // Add Documents section
        if (groupedSources.documents.length > 0) {
            const documentsGroup = document.createElement('optgroup');
            documentsGroup.label = '📄 Documents';
            
            groupedSources.documents.forEach(source => {
                const option = document.createElement('option');
                option.value = `${source.source_type}:${source.source_id}`;
                option.textContent = source.display_name;
                option.title = source.description;
                documentsGroup.appendChild(option);
            });
            
            sourceSelect.appendChild(documentsGroup);
        }
        
        // Add Emails section
        if (groupedSources.emails.length > 0) {
            const emailsGroup = document.createElement('optgroup');
            emailsGroup.label = '📧 Emails';
            
            groupedSources.emails.forEach(source => {
                const option = document.createElement('option');
                option.value = `${source.source_type}:${source.source_id}`;
                option.textContent = source.display_name;
                option.title = source.description;
                emailsGroup.appendChild(option);
            });
            
            sourceSelect.appendChild(emailsGroup);
        }
        
        console.log(`Loaded ${sources.length} sources: ${groupedSources.documents.length} documents, ${groupedSources.emails.length} email types`);
        
    } catch (error) {
        console.error('Error loading sources:', error);
    }
}

async function handleUpload(e) {
    e.preventDefault();
    
    const title = document.getElementById('title').value;
    const description = document.getElementById('description').value;
    const fileInput = document.getElementById('document');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a file to upload');
        return;
    }
    
    const formData = new FormData();
    formData.append('title', title);
    formData.append('description', description);
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_URL}/documents`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Upload failed');
        }
        
        // Reset form
        document.getElementById('upload-form').reset();
        
        // Reload documents and sources
        loadDocuments();
        loadSources();
        
        alert('Document uploaded successfully!');
    } catch (error) {
        alert('Upload failed: ' + error.message);
    }
}

async function deleteDocument(docId) {
    try {
        const response = await fetch(`${API_URL}/documents/${docId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Delete failed');
        }
        
        // Reload documents and sources
        loadDocuments();
        loadSources();
        
        // Reload queries as some might reference this document
        loadQueries();
    } catch (error) {
        alert('Delete failed: ' + error.message);
    }
}

// Query functions
async function handleQuery(e) {
    e.preventDefault();
    
    // START PERFORMANCE TIMING
    const startTime = performance.now();
    console.log('🚀 QUERY STARTED at:', new Date().toISOString());
    
    const question = document.getElementById('question').value;
    const sourceSelection = document.getElementById('source-select').value;
    
    // Parse source selection
    let sourceType = 'all';
    let sourceId = null;
    
    if (sourceSelection) {
        const parts = sourceSelection.split(':');
        sourceType = parts[0];
        sourceId = parts[1];
    }
    
    // Show loading indicator
    const answerContainer = document.getElementById('answer-container');
    const answer = document.getElementById('answer');
    answer.textContent = "Processing your question... This may take a few moments.";
    answerContainer.style.display = 'block';
    
    // Timing checkpoint: UI updated
    const uiUpdateTime = performance.now();
    console.log('📱 UI UPDATED in:', (uiUpdateTime - startTime).toFixed(2), 'ms');
    
    try {
        // Timing checkpoint: Before API call
        const preApiTime = performance.now();
        console.log('🌐 STARTING API CALL at:', (preApiTime - startTime).toFixed(2), 'ms');
        
        const requestBody = {
            question,
            source_type: sourceType,
            source_id: sourceId
        };
        
        console.log('Request body:', requestBody);
        
        const response = await fetch(`${API_URL}/queries`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        // Timing checkpoint: API response received
        const apiResponseTime = performance.now();
        const apiLatency = apiResponseTime - preApiTime;
        console.log('📡 API RESPONSE RECEIVED in:', apiLatency.toFixed(2), 'ms');
        
        if (!response.ok) {
            throw new Error('Query failed');
        }
        
        const data = await response.json();
        
        // Timing checkpoint: JSON parsed
        const jsonParseTime = performance.now();
        console.log('📄 JSON PARSED in:', (jsonParseTime - apiResponseTime).toFixed(2), 'ms');
        
        // Display answer
        document.getElementById('answer').textContent = data.answer;

        // Display sources (attribution)
        const sourcesContainerId = 'answer-sources';
        let sourcesContainer = document.getElementById(sourcesContainerId);
        if (!sourcesContainer) {
            sourcesContainer = document.createElement('div');
            sourcesContainer.id = sourcesContainerId;
            sourcesContainer.className = 'mt-2';
            answerContainer.appendChild(sourcesContainer);
        }
        sourcesContainer.innerHTML = '';
        if (data.sources && data.sources.length > 0) {
            const srcTitle = document.createElement('div');
            srcTitle.className = 'text-muted small mb-1';
            srcTitle.textContent = 'Sources:';
            sourcesContainer.appendChild(srcTitle);
            data.sources.forEach(src => {
                const icon = src.type === 'email' ? '📧' : '📄';
                const label = src.label || (src.type === 'email' ? `Email ${src.id}` : `Document ${src.id}`);
                const pill = document.createElement('span');
                pill.className = 'badge rounded-pill bg-light text-dark me-2';
                pill.textContent = `${icon} ${label}`;
                sourcesContainer.appendChild(pill);
            });
        }
        
        // FINAL PERFORMANCE TIMING
        const endTime = performance.now();
        const totalTime = endTime - startTime;
        
        console.log('✅ QUERY COMPLETED');
        console.log('⏱️  PERFORMANCE BREAKDOWN:');
        console.log('   • UI Update:', (uiUpdateTime - startTime).toFixed(2), 'ms');
        console.log('   • API Call:', apiLatency.toFixed(2), 'ms');
        console.log('   • JSON Parse:', (jsonParseTime - apiResponseTime).toFixed(2), 'ms');
        console.log('   • DOM Update:', (endTime - jsonParseTime).toFixed(2), 'ms');
        console.log('   🎯 TOTAL TIME:', totalTime.toFixed(2), 'ms');
        console.log('   📊 BREAKDOWN: API(' + ((apiLatency/totalTime)*100).toFixed(1) + '%) UI(' + (((totalTime-apiLatency)/totalTime)*100).toFixed(1) + '%)');
        
        // Add timing info to the UI
        const timingInfo = document.createElement('div');
        timingInfo.className = 'timing-info mt-2 text-muted small';
        timingInfo.innerHTML = `
            <details>
                <summary>⏱️ Performance: ${totalTime.toFixed(0)}ms total</summary>
                <div class="mt-1">
                    • API Response: ${apiLatency.toFixed(0)}ms<br>
                    • UI Processing: ${(totalTime - apiLatency).toFixed(0)}ms<br>
                    • Cache: ${data.from_cache ? '✅ Hit' : '❌ Miss'}
                </div>
            </details>
        `;
        
        // Remove any existing timing info
        const existingTiming = answerContainer.querySelector('.timing-info');
        if (existingTiming) {
            existingTiming.remove();
        }
        
        answerContainer.appendChild(timingInfo);
        
        // Reload queries to include the new one
        loadQueries();
        
        // Refresh chat history to show the new query
        chatHistoryOffset = 0; // Reset offset for fresh load
        hasMoreChatHistory = true;
        await loadChatHistory(20, 0);
    } catch (error) {
        const errorTime = performance.now();
        const totalErrorTime = errorTime - startTime;
        
        answer.textContent = `Error: ${error.message}. Please try again.`;
        console.error('❌ QUERY FAILED after:', totalErrorTime.toFixed(2), 'ms');
        console.error('Query failed:', error);
    }
}

async function loadQueries() {
    try {
        const response = await fetch(`${API_URL}/queries`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load queries');
        }
        
        const queries = await response.json();
        
        const queriesList = document.getElementById('queries-list');
        queriesList.innerHTML = '';
        
        if (queries.length === 0) {
            queriesList.innerHTML = '<p class="text-muted">No queries yet.</p>';
        } else {
            queries.forEach(query => {
                const item = document.createElement('div');
                item.className = 'query-item';
                item.innerHTML = `
                    <div class="query-question">${query.question}</div>
                    <div class="query-answer">${query.answer}</div>
                    <div class="query-meta">
                        ${new Date(query.created_at).toLocaleString()}
                        ${query.document_id ? `| Document ID: ${query.document_id}` : '| All documents'}
                    </div>
                `;
                queriesList.appendChild(item);
            });
        }
    } catch (error) {
        console.error('Error loading queries:', error);
    }
}

// Chat history functionality for legacy frontend
let chatHistoryOffset = 0;
let hasMoreChatHistory = true;

async function loadChatHistory(limit = 20, offset = 0) {
    try {
        console.log(`Loading chat history: limit=${limit}, offset=${offset}`);
        
        const params = new URLSearchParams();
        params.append('limit', limit.toString());
        params.append('offset', offset.toString());
        
        const response = await fetch(`${API_URL}/queries?${params.toString()}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load chat history');
        }
        
        const queries = await response.json();
        console.log(`Loaded ${queries.length} chat history queries`);
        
        const chatHistoryContainer = document.getElementById('chat-history');
        if (!chatHistoryContainer) {
            console.warn('Chat history container not found');
            return;
        }
        
        if (offset === 0) {
            // Initial load - clear existing content
            chatHistoryContainer.innerHTML = '';
        }
        
        if (queries.length === 0) {
            if (offset === 0) {
                chatHistoryContainer.innerHTML = '<p class="text-muted">No chat history yet. Start a conversation!</p>';
            }
            hasMoreChatHistory = false;
            return;
        }
        
        // Convert queries to chat messages and append to container
        queries.reverse().forEach(query => { // Reverse to show oldest first
            // User message
            const userMsg = document.createElement('div');
            userMsg.className = 'chat-message user-message mb-2';
            userMsg.innerHTML = `
                <div class="d-flex justify-content-end">
                    <div class="bg-primary text-white p-2 rounded" style="max-width: 80%;">
                        <small class="text-light">${new Date(query.created_at).toLocaleString()}</small>
                        <div>${query.question}</div>
                    </div>
                </div>
            `;
            chatHistoryContainer.appendChild(userMsg);
            
            // Assistant message
            if (query.answer) {
                const assistantMsg = document.createElement('div');
                assistantMsg.className = 'chat-message assistant-message mb-3';
                assistantMsg.innerHTML = `
                    <div class="d-flex justify-content-start">
                        <div class="bg-light text-dark p-2 rounded" style="max-width: 80%;">
                            <small class="text-muted">AI Assistant</small>
                            <div>${query.answer}</div>
                        </div>
                    </div>
                `;
                chatHistoryContainer.appendChild(assistantMsg);
            }
        });
        
        chatHistoryOffset += queries.length;
        hasMoreChatHistory = queries.length === limit;
        
        // Add "Load More" button if there's more history
        updateLoadMoreButton();
        
    } catch (error) {
        console.error('Error loading chat history:', error);
        const chatHistoryContainer = document.getElementById('chat-history');
        if (chatHistoryContainer && offset === 0) {
            chatHistoryContainer.innerHTML = '<p class="text-danger">Failed to load chat history.</p>';
        }
    }
}

function updateLoadMoreButton() {
    const chatHistoryContainer = document.getElementById('chat-history');
    if (!chatHistoryContainer) return;
    
    // Remove existing load more button
    const existingButton = chatHistoryContainer.querySelector('.load-more-history');
    if (existingButton) {
        existingButton.remove();
    }
    
    // Add new load more button if there's more history
    if (hasMoreChatHistory) {
        const loadMoreBtn = document.createElement('div');
        loadMoreBtn.className = 'load-more-history text-center mt-3';
        loadMoreBtn.innerHTML = `
            <button class="btn btn-outline-secondary btn-sm" onclick="loadMoreChatHistory()">
                Load More History
            </button>
        `;
        chatHistoryContainer.appendChild(loadMoreBtn);
    }
}

async function loadMoreChatHistory() {
    if (!hasMoreChatHistory) return;
    
    const loadMoreBtn = document.querySelector('.load-more-history button');
    if (loadMoreBtn) {
        loadMoreBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Loading...';
        loadMoreBtn.disabled = true;
    }
    
    await loadChatHistory(20, chatHistoryOffset);
    
    if (loadMoreBtn) {
        loadMoreBtn.innerHTML = 'Load More History';
        loadMoreBtn.disabled = false;
    }
}

// Helper functions
function showLoginSection() {
    console.log("Showing login section");
    
    // Ensure DOM elements are initialized
    if (!loginSection || !registerSection || !appSection) {
        console.warn("DOM elements not initialized, attempting to initialize...");
        initDOMElements();
    }
    
    // Check if elements exist before accessing them
    if (loginSection) {
        loginSection.style.display = 'block';
    } else {
        console.error("Login section element not found!");
    }
    
    if (registerSection) {
        registerSection.style.display = 'none';
    } else {
        console.error("Register section element not found!");
    }
    
    if (appSection) {
        appSection.style.display = 'none';
    } else {
        console.error("App section element not found!");
    }
}

// Global logout function that can be called from anywhere
function logout() {
    console.log("🔴 Global logout function called");
    try {
        // Log current state before logout
        console.log("📊 Before logout state:", {
            token: token,
            tokenInStorage: localStorage.getItem('token'),
            loginSectionVisible: loginSection ? loginSection.style.display : 'N/A',
            appSectionVisible: appSection ? appSection.style.display : 'N/A',
            registerSectionVisible: registerSection ? registerSection.style.display : 'N/A'
        });
        
        // Remove token from localStorage
        localStorage.removeItem('token');
        token = null;
        
        console.log("🔑 Token removed from localStorage and global variable");
        
        // Show login section
        console.log("🏠 Attempting to show login section...");
        showLoginSection();
        
        // Log state after logout
        console.log("📊 After logout state:", {
            token: token,
            tokenInStorage: localStorage.getItem('token'),
            loginSectionVisible: loginSection ? loginSection.style.display : 'N/A',
            appSectionVisible: appSection ? appSection.style.display : 'N/A',
            registerSectionVisible: registerSection ? registerSection.style.display : 'N/A'
        });
        
        console.log("✅ Logout completed successfully");
        return true;
    } catch (error) {
        console.error("❌ Error during logout:", error);
        return false;
    }
}

// Make logout function available globally
window.logout = logout;

// Debug function to test logout functionality
window.debugLogout = function() {
    console.log("=== LOGOUT DEBUG START ===");
    
    // Check if logout button exists
    const logoutBtn = document.getElementById('logout-btn');
    console.log("1. Logout button found:", logoutBtn);
    
    if (logoutBtn) {
        console.log("2. Button attributes:", {
            id: logoutBtn.id,
            className: logoutBtn.className,
            style: logoutBtn.style.cssText,
            display: window.getComputedStyle(logoutBtn).display,
            visibility: window.getComputedStyle(logoutBtn).visibility,
            disabled: logoutBtn.disabled,
            parentVisible: logoutBtn.parentElement ? window.getComputedStyle(logoutBtn.parentElement).display : 'no parent'
        });
        
        console.log("3. Attempting programmatic click...");
        logoutBtn.click();
        console.log("4. Programmatic click completed");
    }
    
    // Check if global logout function exists
    console.log("5. Global logout function exists:", typeof window.logout);
    if (typeof window.logout === 'function') {
        console.log("6. Attempting to call global logout directly...");
        try {
            window.logout();
            console.log("7. Global logout called successfully");
        } catch (error) {
            console.error("7. Error calling global logout:", error);
        }
    }
    
    console.log("=== LOGOUT DEBUG END ===");
};

function showAppSection() {
    console.log("Showing app section");
    
    // Ensure DOM elements are initialized
    if (!loginSection || !registerSection || !appSection) {
        console.warn("DOM elements not initialized, attempting to initialize...");
        initDOMElements();
    }
    
    // Check if elements exist before accessing them
    if (loginSection) {
        loginSection.style.display = 'none';
    } else {
        console.error("Login section element not found!");
    }
    
    if (registerSection) {
        registerSection.style.display = 'none';
    } else {
        console.error("Register section element not found!");
    }
    
    if (appSection) {
        appSection.style.display = 'block';
    } else {
        console.error("App section element not found!");
    }
    
    // Initialize Gmail UI after app section is shown
    setTimeout(() => {
        initializeGmailUI();
        debugGmailButton();
    }, 100);
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' bytes';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    else return (bytes / 1048576).toFixed(1) + ' MB';
}

function getCategoryInfo(documentType) {
    const categories = {
        'financial': {
            label: 'Financial',
            icon: '💰',
            badgeClass: 'bg-success',
            processingNote: 'Precise transaction matching'
        },
        'long_form': {
            label: 'Long-form',
            icon: '📚',
            badgeClass: 'bg-primary',
            processingNote: 'Deep semantic analysis'
        },
        'generic': {
            label: 'Generic',
            icon: '📄',
            badgeClass: 'bg-secondary',
            processingNote: 'Balanced processing'
        }
    };
    
    return categories[documentType] || categories['generic'];
}

// Debug functions
async function updateDebugInfo() {
    console.log("Updating debug info...");
    
    // Update JavaScript status
    const debugJs = document.getElementById('debug-js');
    if (debugJs) {
        debugJs.innerHTML = 'JavaScript: <span class="badge bg-success">Working</span>';
    }
    
    // Update DOM Elements status
    const debugDom = document.getElementById('debug-dom');
    if (debugDom) {
        const elementsFound = loginSection && registerSection && appSection;
        const status = elementsFound ? 'bg-success">Found' : 'bg-danger">Missing';
        debugDom.innerHTML = `DOM Elements: <span class="badge ${status}</span>`;
    }
    
    // Update API Connection status
    const debugApi = document.getElementById('debug-api');
    if (debugApi) {
        try {
            debugApi.innerHTML = 'API Connection: <span class="badge bg-warning">Testing...</span>';
            
            const response = await fetch(`${API_URL}/health-check`, {
                method: 'GET',
                timeout: 5000
            });
            
            if (response.ok) {
                const data = await response.json();
                debugApi.innerHTML = `API Connection: <span class="badge bg-success">OK (v${data.version})</span>`;
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('API connection test failed:', error);
            debugApi.innerHTML = `API Connection: <span class="badge bg-danger">Failed (${error.message})</span>`;
        }
    }
    
    // Update Authentication status
    const debugAuth = document.getElementById('debug-auth');
    if (debugAuth) {
        const authStatus = token ? 'bg-success">Logged In' : 'bg-warning">Not Logged In';
        debugAuth.innerHTML = `Authentication: <span class="badge ${authStatus}</span>`;
    }
}

// Initialize debug info on page load
document.addEventListener('DOMContentLoaded', () => {
    // Add small delay to ensure elements are ready
    setTimeout(updateDebugInfo, 1000);
    
    // Add refresh button functionality
    const debugRefreshBtn = document.getElementById('debug-refresh');
    if (debugRefreshBtn) {
        debugRefreshBtn.addEventListener('click', updateDebugInfo);
    }
});

// Gmail functionality
async function initializeGmailUI() {
    try {
        console.log('Initializing Gmail UI...');
        
        // Check if user is logged in
        if (!token) {
            console.log('No token found, skipping Gmail initialization');
            return;
        }
        
        // Check if app section is visible
        const appSection = document.getElementById('app-section');
        if (!appSection || appSection.style.display === 'none') {
            console.log('App section not visible, skipping Gmail initialization');
            return;
        }
        
        // Add event listeners for Gmail buttons
        const connectGmailBtn = document.getElementById('connect-gmail-btn');
        const disconnectGmailBtn = document.getElementById('disconnect-gmail-btn');
        const syncEmailsBtn = document.getElementById('sync-emails-btn');
        const searchEmailsBtn = document.getElementById('search-emails-btn');
        
        console.log('Gmail buttons found:', {
            connectGmailBtn: connectGmailBtn ? 'found' : 'missing',
            disconnectGmailBtn: disconnectGmailBtn ? 'found' : 'missing',
            syncEmailsBtn: syncEmailsBtn ? 'found' : 'missing',
            searchEmailsBtn: searchEmailsBtn ? 'found' : 'missing'
        });
        
        // Use event delegation as backup
        document.addEventListener('click', function(e) {
            if (e.target && e.target.id === 'connect-gmail-btn') {
                console.log('Connect Gmail clicked via event delegation');
                e.preventDefault();
                connectGmail();
            }
        });
        
        if (connectGmailBtn) {
            // Remove any existing listeners first
            connectGmailBtn.removeEventListener('click', connectGmail);
            
            connectGmailBtn.addEventListener('click', (e) => {
                console.log('Connect Gmail button clicked - direct event fired!');
                e.preventDefault();
                connectGmail();
            });
            console.log('Connect Gmail button event listener added');
        }
        
        if (disconnectGmailBtn) {
            disconnectGmailBtn.addEventListener('click', disconnectGmail);
        }
        
        if (syncEmailsBtn) {
            console.log('✅ Adding sync emails event listener');
            syncEmailsBtn.addEventListener('click', (e) => {
                console.log('🎯 Sync emails button clicked via event listener');
                e.preventDefault();
                syncEmails();
            });
        } else {
            console.error('❌ Sync emails button not found during initialization');
        }
        
        if (searchEmailsBtn) {
            searchEmailsBtn.addEventListener('click', searchEmails);
        }
        
        // Check Gmail connection status
        await checkGmailStatus();
        
    } catch (error) {
        console.error('Error initializing Gmail UI:', error);
    }
}

async function checkGmailStatus() {
    try {
        const response = await fetch(`${API_URL}/gmail/accounts`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to check Gmail status');
        }
        
        const accounts = await response.json();
        
        if (accounts.length > 0) {
            const account = accounts[0]; // Use first account
            await updateGmailUI(account);
        } else {
            showGmailNotConnected();
        }
        
    } catch (error) {
        console.error('Error checking Gmail status:', error);
        showGmailNotConnected();
    }
}

async function updateGmailUI(account) {
    try {
        // Get account status
        const response = await fetch(`${API_URL}/gmail/status/${account.id}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to get Gmail status');
        }
        
        const status = await response.json();
        
        // Update UI elements
        const connectionStatus = document.getElementById('gmail-connection-status');
        const accountEmail = document.getElementById('gmail-account-email');
        const totalEmails = document.getElementById('gmail-total-emails');
        const unreadEmails = document.getElementById('gmail-unread-emails');
        const lastSync = document.getElementById('gmail-last-sync');
        
        const gmailNotConnected = document.getElementById('gmail-not-connected');
        const gmailConnected = document.getElementById('gmail-connected');
        
        if (connectionStatus) {
            connectionStatus.textContent = status.is_connected ? 'Connected' : 'Disconnected';
            connectionStatus.className = status.is_connected ? 'badge bg-success' : 'badge bg-danger';
        }
        
        if (accountEmail) {
            accountEmail.textContent = status.email_address;
        }
        
        if (totalEmails) {
            totalEmails.textContent = status.total_emails;
        }
        
        if (unreadEmails) {
            unreadEmails.textContent = status.unread_emails;
        }
        
        if (lastSync) {
            lastSync.textContent = status.last_sync_at ? 
                new Date(status.last_sync_at).toLocaleString() : 'Never';
        }
        
        // Show/hide sections
        if (gmailNotConnected) {
            gmailNotConnected.style.display = 'none';
        }
        
        if (gmailConnected) {
            gmailConnected.style.display = 'block';
        }
        
    } catch (error) {
        console.error('Error updating Gmail UI:', error);
        showGmailNotConnected();
    }
}

function showGmailNotConnected() {
    const connectionStatus = document.getElementById('gmail-connection-status');
    const gmailNotConnected = document.getElementById('gmail-not-connected');
    const gmailConnected = document.getElementById('gmail-connected');
    
    if (connectionStatus) {
        connectionStatus.textContent = 'Not Connected';
        connectionStatus.className = 'badge bg-warning';
    }
    
    if (gmailNotConnected) {
        gmailNotConnected.style.display = 'block';
    }
    
    if (gmailConnected) {
        gmailConnected.style.display = 'none';
    }
}

async function connectGmail() {
    try {
        console.log('Connect Gmail button clicked! [VERSION 4.0 - SESSION BASED]');
        console.log('Current token:', token ? 'present' : 'missing');
        
        // Check if we have a valid token
        if (!token) {
            alert('You need to be logged in to connect Gmail. Please refresh the page and login again.');
            return;
        }
        
        // Redirect with token as cookie or query parameter
        // The backend will handle authentication via session/cookie
        window.location.href = `${API_URL}/gmail/auth?token=${encodeURIComponent(token)}`;
        
    } catch (error) {
        console.error('Error connecting Gmail:', error);
        alert('Failed to connect Gmail. Please try again.');
    }
}

async function disconnectGmail() {
    try {
        // Get current account
        const accountsResponse = await fetch(`${API_URL}/gmail/accounts`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!accountsResponse.ok) {
            throw new Error('Failed to get Gmail accounts');
        }
        
        const accounts = await accountsResponse.json();
        
        if (accounts.length === 0) {
            showGmailNotConnected();
            return;
        }
        
        const account = accounts[0];
        
        // Disconnect account
        const response = await fetch(`${API_URL}/gmail/disconnect/${account.id}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to disconnect Gmail');
        }
        
        showGmailNotConnected();
        alert('Gmail account disconnected successfully');
        
    } catch (error) {
        console.error('Error disconnecting Gmail:', error);
        alert('Failed to disconnect Gmail. Please try again.');
    }
}

async function syncEmails() {
    try {
        console.log('🔄 Sync Emails button clicked!');
        
        const syncBtn = document.getElementById('sync-emails-btn');
        console.log('Sync button element:', syncBtn ? 'found' : 'missing');
        
        if (syncBtn) {
            syncBtn.disabled = true;
            syncBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Syncing...';
        }
        
        // Get current account
        const accountsResponse = await fetch(`${API_URL}/gmail/accounts`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!accountsResponse.ok) {
            throw new Error('Failed to get Gmail accounts');
        }
        
        const accounts = await accountsResponse.json();
        
        if (accounts.length === 0) {
            throw new Error('No Gmail account connected');
        }
        
        const account = accounts[0];
        
        // Sync emails with timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minute timeout
        
        console.log(`🔄 Starting sync for account ${account.id} (max 100 emails)`);
        
        const syncResponse = await fetch(`${API_URL}/gmail/sync`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                account_id: account.id,
                max_emails: 100
            }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!syncResponse.ok) {
            const errorText = await syncResponse.text();
            console.error('Sync failed:', errorText);
            throw new Error(`Failed to sync emails: ${syncResponse.status} ${syncResponse.statusText}`);
        }
        
        const syncData = await syncResponse.json();
        console.log('✅ Sync completed:', syncData);
        
        alert(`Successfully synced ${syncData.emails_synced} emails`);
        
        // Update Gmail status
        await checkGmailStatus();
        
    } catch (error) {
        console.error('Error syncing emails:', error);
        
        if (error.name === 'AbortError') {
            alert('Sync timed out after 2 minutes. Please try again or check your internet connection.');
        } else {
            alert(`Failed to sync emails: ${error.message}`);
        }
    } finally {
        const syncBtn = document.getElementById('sync-emails-btn');
        if (syncBtn) {
            syncBtn.disabled = false;
            syncBtn.innerHTML = '<i class="fas fa-sync"></i> Sync Emails';
        }
    }
}

async function searchEmails() {
    try {
        const query = document.getElementById('email-search-query').value.trim();
        if (!query) {
            alert('Please enter a search query');
            return;
        }
        
        const searchBtn = document.getElementById('search-emails-btn');
        if (searchBtn) {
            searchBtn.disabled = true;
            searchBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
        }
        
        // Get filter values
        const emailType = document.getElementById('email-type-filter').value;
        const senderEmail = document.getElementById('email-sender-filter').value;
        const dateFrom = document.getElementById('email-date-from').value;
        const dateTo = document.getElementById('email-date-to').value;
        
        // Build search request
        const searchRequest = {
            query: query,
            limit: 20
        };
        
        if (emailType) searchRequest.email_type = emailType;
        if (senderEmail) searchRequest.sender_email = senderEmail;
        if (dateFrom) searchRequest.date_from = dateFrom;
        if (dateTo) searchRequest.date_to = dateTo;
        
        // Search emails
        const response = await fetch(`${API_URL}/gmail/search`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(searchRequest)
        });
        
        if (!response.ok) {
            throw new Error('Failed to search emails');
        }
        
        const searchData = await response.json();
        
        // Display results
        displayEmailSearchResults(searchData.emails, searchData.processing_time_ms);
        
    } catch (error) {
        console.error('Error searching emails:', error);
        alert('Failed to search emails. Please try again.');
    } finally {
        const searchBtn = document.getElementById('search-emails-btn');
        if (searchBtn) {
            searchBtn.disabled = false;
            searchBtn.innerHTML = '<i class="fas fa-search"></i> Search Emails';
        }
    }
}

function displayEmailSearchResults(emails, processingTime) {
    const resultsContainer = document.getElementById('email-search-results');
    const resultsList = document.getElementById('email-results-list');
    
    if (!resultsContainer || !resultsList) {
        return;
    }
    
    // Clear previous results
    resultsList.innerHTML = '';
    
    if (emails.length === 0) {
        resultsList.innerHTML = '<div class="list-group-item">No emails found matching your search criteria.</div>';
    } else {
        emails.forEach(email => {
            const item = document.createElement('div');
            item.className = 'list-group-item';
            
            // Format date
            const sentDate = new Date(email.sent_at).toLocaleString();
            
            // Get email type badge
            const typeBadge = getEmailTypeBadge(email.email_type);
            
            item.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${email.subject}</h6>
                    <small>${sentDate}</small>
                </div>
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <small class="text-muted">From: ${email.sender_email}</small>
                    ${typeBadge}
                </div>
                <p class="mb-1">${truncateText(email.body_text, 150)}</p>
                <small class="text-muted">
                    ${email.is_read ? '✓ Read' : '● Unread'}
                </small>
            `;
            
            resultsList.appendChild(item);
        });
    }
    
    // Add processing time info
    const timingInfo = document.createElement('div');
    timingInfo.className = 'text-muted small mt-2';
    timingInfo.textContent = `Found ${emails.length} results in ${processingTime}ms`;
    resultsList.appendChild(timingInfo);
    
    // Show results container
    resultsContainer.style.display = 'block';
}

function getEmailTypeBadge(emailType) {
    const badges = {
        'business': '<span class="badge bg-primary">Business</span>',
        'personal': '<span class="badge bg-success">Personal</span>',
        'promotional': '<span class="badge bg-warning">Promotional</span>',
        'transactional': '<span class="badge bg-info">Transactional</span>',
        'support': '<span class="badge bg-secondary">Support</span>',
        'generic': '<span class="badge bg-light text-dark">Generic</span>'
    };
    
    return badges[emailType] || badges['generic'];
}

function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Debug function to test Gmail button manually
function testGmailButton() {
    console.log('Testing Gmail button manually...');
    const btn = document.getElementById('connect-gmail-btn');
    console.log('Button found:', btn ? 'yes' : 'no');
    if (btn) {
        console.log('Button text:', btn.textContent);
        console.log('Button disabled:', btn.disabled);
        console.log('Button style.display:', btn.style.display);
        btn.style.border = '3px solid red'; // Visual indicator
        btn.click();
    }
}

// Add a simple button test on page load
function debugGmailButton() {
    setTimeout(() => {
        console.log('=== GMAIL BUTTON DEBUG ===');
        const btn = document.getElementById('connect-gmail-btn');
        if (btn) {
            console.log('✓ Button exists');
            console.log('Text:', btn.textContent);
            console.log('Disabled:', btn.disabled);
            console.log('Parent visible:', btn.parentElement.style.display !== 'none');
            
            // Add a temporary border to make it obvious
            btn.style.border = '2px solid blue';
            
            // Test click programmatically
            btn.addEventListener('click', function() {
                console.log('✓ Button click detected!');
            });
        } else {
            console.log('✗ Button not found');
        }
    }, 2000);
}

// Make functions available globally for debugging
window.testGmailButton = testGmailButton;
window.connectGmail = connectGmail;
window.initializeGmailUI = initializeGmailUI;
window.syncEmails = syncEmails;

// Helper function to manually test sync
window.testSync = async function() {
    console.log('🧪 Testing sync manually...');
    try {
        await syncEmails();
    } catch (error) {
        console.error('Manual sync test failed:', error);
    }
}; 
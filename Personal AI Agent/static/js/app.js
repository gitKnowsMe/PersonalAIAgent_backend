// Global variables
let token = localStorage.getItem('token');
const API_URL = window.location.origin + '/api';

// Debug message
console.log("App.js loaded successfully!");
console.log("Using API URL:", API_URL);

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
    
    // Check if user is logged in
    if (token) {
        console.log("User is logged in with token:", token);
        showAppSection();
        loadDocuments();
        loadQueries();
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
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                localStorage.removeItem('token');
                token = null;
                showLoginSection();
            });
        } else {
            console.error("Logout button not found!");
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
        
        const documentSelect = document.getElementById('document-select');
        // Keep the "All Documents" option
        documentSelect.innerHTML = '<option value="">All Documents</option>';
        
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
                
                // Add to document select dropdown
                const option = document.createElement('option');
                option.value = doc.id;
                option.textContent = doc.title;
                documentSelect.appendChild(option);
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
        
        // Reload documents
        loadDocuments();
        
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
        
        // Reload documents
        loadDocuments();
        
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
    const documentId = document.getElementById('document-select').value;
    
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
        
        const response = await fetch(`${API_URL}/queries`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question,
                document_id: documentId || null
            })
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

// Helper functions
function showLoginSection() {
    console.log("Showing login section");
    loginSection.style.display = 'block';
    registerSection.style.display = 'none';
    appSection.style.display = 'none';
}

function showAppSection() {
    console.log("Showing app section");
    loginSection.style.display = 'none';
    registerSection.style.display = 'none';
    appSection.style.display = 'block';
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
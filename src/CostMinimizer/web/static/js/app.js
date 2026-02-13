// CostMinimizer Web Interface JavaScript

let credentialsValidated = false;
let currentRegion = 'us-east-1';

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    loadAvailableReports();
});

function setupEventListeners() {
    // Credentials form
    document.getElementById('credentials-form').addEventListener('submit', handleCredentialsSubmit);
    
    // Reports button
    document.getElementById('run-reports-btn').addEventListener('click', handleRunReports);
    
    // Chat button
    document.getElementById('send-chat-btn').addEventListener('click', handleSendChat);
    
    // Chat input enter key
    document.getElementById('chat-input').addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.ctrlKey) {
            handleSendChat();
        }
    });
    
    // Copy docker command
    document.getElementById('copy-docker-btn').addEventListener('click', copyDockerCommand);
}

async function handleCredentialsSubmit(e) {
    e.preventDefault();
    
    const formData = {
        access_key: document.getElementById('access-key').value,
        secret_key: document.getElementById('secret-key').value,
        session_token: document.getElementById('session-token').value,
        region: document.getElementById('region').value
    };
    
    currentRegion = formData.region;
    
    showStatus('credentials-status', 'Validating credentials...', 'info');
    
    try {
        const response = await fetch('/api/validate-credentials', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            credentialsValidated = true;
            showStatus('credentials-status', 
                `✅ Credentials validated successfully!<br>Account: ${result.account_id}<br>User: ${result.user_arn}`, 
                'success');
            
            // Show other sections
            document.getElementById('reports-section').style.display = 'block';
            document.getElementById('chat-section').style.display = 'block';
            document.getElementById('docker-section').style.display = 'block';
            
            // Generate docker command
            generateDockerCommand();
            
            // Add welcome message to chat
            addChatMessage('system', 'Welcome! Your AWS credentials have been validated. You can now generate reports or ask me questions about AWS cost optimization.');
        } else {
            showStatus('credentials-status', `❌ Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showStatus('credentials-status', `❌ Error: ${error.message}`, 'error');
    }
}

async function handleRunReports() {
    if (!credentialsValidated) {
        showStatus('reports-status', '❌ Please validate credentials first', 'error');
        return;
    }
    
    const selectedReports = [];
    document.querySelectorAll('.report-card input[type="checkbox"]:checked').forEach(checkbox => {
        selectedReports.push(checkbox.value);
    });
    
    if (selectedReports.length === 0) {
        showStatus('reports-status', '❌ Please select at least one report', 'error');
        return;
    }
    
    const runButton = document.getElementById('run-reports-btn');
    runButton.disabled = true;
    runButton.textContent = 'Generating Reports...';
    
    showStatus('reports-status', 
        `🚀 Generating reports: ${selectedReports.join(', ').toUpperCase()}<br>This may take several minutes...`, 
        'info');
    
    try {
        const response = await fetch('/api/run-reports', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                reports: selectedReports,
                region: currentRegion
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus('reports-status', 
                `✅ Reports generated successfully!<br>` +
                `📊 Reports: ${result.reports_generated.join(', ').toUpperCase()}<br>` +
                `📁 Output folder: ${result.output_folder}<br>` +
                `💡 You can now ask questions about the results in the chat below.`, 
                'success');
            
            // Add message to chat
            addChatMessage('system', `Reports generated successfully! Output saved to: ${result.output_folder}`);
        } else {
            showStatus('reports-status', `❌ Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showStatus('reports-status', `❌ Error: ${error.message}`, 'error');
    } finally {
        runButton.disabled = false;
        runButton.textContent = 'Generate Reports';
    }
}

async function handleSendChat() {
    if (!credentialsValidated) {
        addChatMessage('system', '❌ Please validate credentials first');
        return;
    }
    
    const chatInput = document.getElementById('chat-input');
    const message = chatInput.value.trim();
    
    if (!message) {
        return;
    }
    
    // Add user message to chat
    addChatMessage('user', message);
    chatInput.value = '';
    
    // Show loading
    const loadingId = 'loading-' + Date.now();
    addChatMessage('assistant', '<div class="spinner"></div>', loadingId);
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message
            })
        });
        
        const result = await response.json();
        
        // Remove loading message
        const loadingElement = document.getElementById(loadingId);
        if (loadingElement) {
            loadingElement.remove();
        }
        
        if (result.success) {
            addChatMessage('assistant', result.answer);
        } else {
            addChatMessage('assistant', `❌ Error: ${result.error}`);
        }
    } catch (error) {
        // Remove loading message
        const loadingElement = document.getElementById(loadingId);
        if (loadingElement) {
            loadingElement.remove();
        }
        addChatMessage('assistant', `❌ Error: ${error.message}`);
    }
}

function addChatMessage(type, content, id = null) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}`;
    if (id) {
        messageDiv.id = id;
    }
    messageDiv.innerHTML = content;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

async function loadAvailableReports() {
    try {
        const response = await fetch('/api/available-reports');
        const result = await response.json();
        
        if (result.success) {
            console.log('Available reports:', result.reports);
        }
    } catch (error) {
        console.error('Error loading available reports:', error);
    }
}

async function generateDockerCommand() {
    const selectedReports = [];
    document.querySelectorAll('.report-card input[type="checkbox"]:checked').forEach(checkbox => {
        selectedReports.push(checkbox.value);
    });
    
    try {
        const response = await fetch('/api/docker-command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                reports: selectedReports.length > 0 ? selectedReports : ['ce', 'ta', 'co'],
                region: currentRegion
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            document.getElementById('docker-command').textContent = result.command;
        }
    } catch (error) {
        console.error('Error generating docker command:', error);
    }
}

function copyDockerCommand() {
    const command = document.getElementById('docker-command').textContent;
    navigator.clipboard.writeText(command).then(() => {
        const btn = document.getElementById('copy-docker-btn');
        const originalText = btn.textContent;
        btn.textContent = '✅ Copied!';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    });
}

function showStatus(elementId, message, type) {
    const statusElement = document.getElementById(elementId);
    statusElement.innerHTML = message;
    statusElement.className = `status-message ${type}`;
    statusElement.style.display = 'block';
}

// Update docker command when report selection changes
document.addEventListener('change', function(e) {
    if (e.target.matches('.report-card input[type="checkbox"]')) {
        if (credentialsValidated) {
            generateDockerCommand();
        }
    }
});

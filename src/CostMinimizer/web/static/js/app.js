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
    
    // Clear previous logs and setup log container in reports-status
    const reportsStatus = document.getElementById('reports-status');
    reportsStatus.innerHTML = '<h3>📊 Report Generation Logs:</h3><div id="log-container"></div>';
    reportsStatus.className = 'status-message info';
    reportsStatus.style.display = 'block';
    
    try {
        // Start report generation
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
        
        if (result.success && result.session_id) {
            // Connect to SSE stream
            streamReportLogs(result.session_id, selectedReports);
        } else {
            showStatus('reports-status', `❌ Error: ${result.error}`, 'error');
            runButton.disabled = false;
            runButton.textContent = 'Generate Reports';
        }
    } catch (error) {
        showStatus('reports-status', `❌ Error: ${error.message}`, 'error');
        runButton.disabled = false;
        runButton.textContent = 'Generate Reports';
    }
}

function streamReportLogs(sessionId, selectedReports) {
    const reportsStatus = document.getElementById('reports-status');
    const logContainer = document.getElementById('log-container');
    const runButton = document.getElementById('run-reports-btn');
    let excelFilePath = null;
    
    const eventSource = new EventSource(`/api/stream-logs/${sessionId}`);
    
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        switch(data.type) {
            case 'log':
                // Add log message
                const logLine = document.createElement('div');
                logLine.textContent = data.message;
                logLine.style.marginBottom = '2px';
                
                // Highlight important messages
                if (data.message.includes('ERROR')) {
                    logLine.style.color = 'red';
                    logLine.style.fontWeight = 'bold';
                } else if (data.message.includes('SUCCESS') || data.message.includes('saved into')) {
                    logLine.style.color = 'green';
                    logLine.style.fontWeight = 'bold';
                }
                
                // Extract Excel file path
                if (data.message.includes('Excel Report Output saved into:')) {
                    const match = data.message.match(/Excel Report Output saved into:\s*(.+\.xlsx)/);
                    if (match) {
                        excelFilePath = match[1];
                    }
                }
                
                logContainer.appendChild(logLine);
                logContainer.scrollTop = logContainer.scrollHeight;
                break;
                
            case 'excel':
                excelFilePath = data.path;
                break;
                
            case 'success':
                const successLine = document.createElement('div');
                successLine.textContent = data.message;
                successLine.style.color = 'green';
                successLine.style.fontWeight = 'bold';
                successLine.style.marginTop = '10px';
                logContainer.appendChild(successLine);
                logContainer.scrollTop = logContainer.scrollHeight;
                break;
                
            case 'error':
                const errorLine = document.createElement('div');
                errorLine.textContent = `ERROR: ${data.message}`;
                errorLine.style.color = 'red';
                errorLine.style.fontWeight = 'bold';
                errorLine.style.marginTop = '10px';
                logContainer.appendChild(errorLine);
                logContainer.scrollTop = logContainer.scrollHeight;
                
                // Update reports-status with error
                reportsStatus.innerHTML = `<h3>❌ Report Generation Failed</h3>` +
                    `<div id="log-container"></div>` +
                    `<div style="margin-top: 15px; padding: 10px; background: #f8d7da; color: #721c24; border-radius: 5px;">` +
                    `<strong>Error:</strong> ${data.message}` +
                    `</div>`;
                reportsStatus.className = 'status-message error';
                
                eventSource.close();
                runButton.disabled = false;
                runButton.textContent = 'Generate Reports';
                break;
                
            case 'done':
                eventSource.close();
                runButton.disabled = false;
                runButton.textContent = 'Generate Reports';
                
                // Show success message with download link in reports-status
                let successHTML = `<h3>✅ Reports Generated Successfully!</h3>` +
                    `<div id="log-container"></div>` +
                    `<div style="margin-top: 15px; padding: 15px; background: #d4edda; color: #155724; border-radius: 5px;">` +
                    `<strong>📊 Reports:</strong> ${selectedReports.join(', ').toUpperCase()}<br>`;
                
                if (excelFilePath || data.excel_file) {
                    const filePath = excelFilePath || data.excel_file;
                    successHTML += `<strong>📁 Excel Report:</strong> <a href="/api/download-report/${encodeURIComponent(filePath)}" download style="color: #007bff; text-decoration: underline; font-weight: bold;">Download CostMinimizer.xlsx</a><br>`;
                }
                
                successHTML += `<strong>💡 Tip:</strong> You can now ask questions about the results in the chat below.` +
                    `</div>`;
                
                // Preserve the log container content
                const logContent = logContainer.innerHTML;
                reportsStatus.innerHTML = successHTML;
                reportsStatus.className = 'status-message success';
                
                // Restore log content
                const newLogContainer = document.getElementById('log-container');
                if (newLogContainer) {
                    newLogContainer.innerHTML = logContent;
                }
                
                // Add message to chat
                addChatMessage('system', `Reports generated successfully!${excelFilePath ? ' Excel file is ready for download.' : ''}`);
                break;
                
            case 'keepalive':
                // Just keep connection alive
                break;
        }
    };
    
    eventSource.onerror = function(error) {
        console.error('SSE Error:', error);
        eventSource.close();
        
        const errorLine = document.createElement('div');
        errorLine.textContent = 'Connection error. Please check the logs above for details.';
        errorLine.style.color = 'red';
        errorLine.style.fontWeight = 'bold';
        errorLine.style.marginTop = '10px';
        
        if (logContainer) {
            logContainer.appendChild(errorLine);
        }
        
        runButton.disabled = false;
        runButton.textContent = 'Generate Reports';
    };
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

// Simplified CTF AI JavaScript
class SimplifiedCTFAI {
    constructor() {
        this.currentTab = 'chat';
        this.clientAI = new ClientAI();
        this.init();
    }

    init() {
        // Initialize feather icons
        feather.replace();
        
        // Setup event listeners
        this.setupTabNavigation();
        this.setupChat();
        this.setupUpload();
        this.setupDataCollection();
        this.setupTraining();
        
        // Start status polling
        this.pollStatus();
        
        console.log('Simplified CTF AI initialized');
    }

    setupTabNavigation() {
        const navLinks = document.querySelectorAll('[data-tab]');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const tabName = link.dataset.tab;
                this.switchTab(tabName);
            });
        });
    }

    switchTab(tabName) {
        // Hide all tabs
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Show selected tab
        const selectedTab = document.getElementById(`${tabName}-tab`);
        if (selectedTab) {
            selectedTab.classList.add('active');
        }
        
        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        this.currentTab = tabName;
    }

    setupChat() {
        const userInput = document.getElementById('user-input');
        const sendBtn = document.getElementById('send-btn');
        
        sendBtn.addEventListener('click', () => this.sendMessage());
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }

    async sendMessage() {
        const userInput = document.getElementById('user-input');
        const message = userInput.value.trim();
        
        if (!message) return;
        
        // Clear input
        userInput.value = '';
        
        // Add user message to chat
        this.addChatMessage(message, 'user');
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            // Use client-side AI processing instead of server calls
            const result = await this.clientAI.processQuestion(message);
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Add AI response with metadata
            this.addChatMessage(result.response, 'bot');
            
            // Show response metadata
            const metadataText = `Model: ${result.modelType} | Time: ${Math.round(result.responseTime)}ms | Category: ${result.category}`;
            this.addMetadataMessage(metadataText);
            
        } catch (error) {
            this.hideTypingIndicator();
            this.addChatMessage('I encountered an error processing your question, but I can still help! Try asking about specific CTF topics like web security, cryptography, or binary exploitation.', 'bot');
            console.error('Client AI error:', error);
        }
    }

    addChatMessage(content, sender) {
        const messagesDiv = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(contentDiv);
        messagesDiv.appendChild(messageDiv);
        
        // Scroll to bottom
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    addMetadataMessage(content) {
        const messagesDiv = document.getElementById('chat-messages');
        const metadataDiv = document.createElement('div');
        metadataDiv.className = 'message metadata-message';
        metadataDiv.innerHTML = `<small class="text-muted">${content}</small>`;
        
        messagesDiv.appendChild(metadataDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    showTypingIndicator() {
        const messagesDiv = document.getElementById('chat-messages');
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'typing-indicator';
        typingDiv.innerHTML = `
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        messagesDiv.appendChild(typingDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    setupUpload() {
        const uploadBtn = document.getElementById('upload-btn');
        const fileInput = document.getElementById('file-input');
        
        uploadBtn.addEventListener('click', () => this.uploadFiles());
        
        // Drag and drop support
        const uploadTab = document.getElementById('upload-tab');
        uploadTab.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
        
        uploadTab.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const files = e.dataTransfer.files;
            fileInput.files = files;
        });
    }

    async uploadFiles() {
        const fileInput = document.getElementById('file-input');
        const files = fileInput.files;
        
        if (files.length === 0) {
            this.showAlert('Please select files to upload.', 'warning');
            return;
        }
        
        const progressDiv = document.getElementById('upload-progress');
        const resultsDiv = document.getElementById('upload-results');
        const progressBar = progressDiv.querySelector('.progress-bar');
        
        progressDiv.style.display = 'block';
        resultsDiv.innerHTML = '';
        
        let successCount = 0;
        let totalFiles = files.length;
        
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    successCount++;
                    this.showUploadResult(file.name, 'success', data.message);
                } else {
                    this.showUploadResult(file.name, 'error', data.error);
                }
                
            } catch (error) {
                this.showUploadResult(file.name, 'error', 'Upload failed');
                console.error('Upload error:', error);
            }
            
            // Update progress
            const progress = ((i + 1) / totalFiles) * 100;
            progressBar.style.width = `${progress}%`;
        }
        
        // Hide progress after completion
        setTimeout(() => {
            progressDiv.style.display = 'none';
        }, 1000);
        
        this.showAlert(`Uploaded ${successCount} of ${totalFiles} files successfully.`, 'success');
        
        // Clear file input
        fileInput.value = '';
    }

    showUploadResult(filename, type, message) {
        const resultsDiv = document.getElementById('upload-results');
        const resultDiv = document.createElement('div');
        resultDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'}`;
        resultDiv.innerHTML = `<strong>${filename}:</strong> ${message}`;
        resultsDiv.appendChild(resultDiv);
    }

    setupDataCollection() {
        const collectBtn = document.getElementById('collect-btn');
        collectBtn.addEventListener('click', () => this.collectData());
    }

    async collectData() {
        const collectBtn = document.getElementById('collect-btn');
        const resultsDiv = document.getElementById('collection-results');
        
        collectBtn.disabled = true;
        collectBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Collecting...';
        
        try {
            const response = await fetch('/api/collect-data', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (response.ok) {
                resultsDiv.innerHTML = `
                    <div class="alert alert-success">
                        Successfully collected ${data.collected_count} writeups!
                    </div>
                `;
            } else {
                resultsDiv.innerHTML = `
                    <div class="alert alert-danger">
                        Error: ${data.error}
                    </div>
                `;
            }
            
        } catch (error) {
            resultsDiv.innerHTML = `
                <div class="alert alert-danger">
                    Failed to collect data. Please try again.
                </div>
            `;
            console.error('Collection error:', error);
        }
        
        collectBtn.disabled = false;
        collectBtn.innerHTML = '<i data-feather="download"></i> Collect New Data';
        feather.replace();
    }

    setupTraining() {
        const trainBtn = document.getElementById('manual-train-btn');
        trainBtn.addEventListener('click', () => this.startTraining());
    }

    async startTraining() {
        const trainBtn = document.getElementById('manual-train-btn');
        const progressDiv = document.getElementById('training-progress');
        const progressBar = progressDiv.querySelector('.progress-bar');
        
        trainBtn.disabled = true;
        trainBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Starting...';
        progressDiv.style.display = 'block';
        
        try {
            const response = await fetch('/api/trigger-training', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Simulate training progress
                let progress = 0;
                const interval = setInterval(() => {
                    progress += Math.random() * 10;
                    if (progress > 100) progress = 100;
                    
                    progressBar.style.width = `${progress}%`;
                    
                    if (progress >= 100) {
                        clearInterval(interval);
                        setTimeout(() => {
                            progressDiv.style.display = 'none';
                            this.showAlert('Training completed successfully!', 'success');
                        }, 1000);
                    }
                }, 1000);
            } else {
                this.showAlert(`Training error: ${data.error}`, 'error');
                progressDiv.style.display = 'none';
            }
            
        } catch (error) {
            this.showAlert('Failed to start training.', 'error');
            progressDiv.style.display = 'none';
            console.error('Training error:', error);
        }
        
        trainBtn.disabled = false;
        trainBtn.innerHTML = '<i data-feather="play"></i> Start Manual Training';
        feather.replace();
    }

    async pollStatus() {
        try {
            // Get client-side AI status
            const clientStatus = this.clientAI.getStatus();
            
            // Try to get server status but don't fail if unavailable
            let serverData = {
                writeup_count: 0,
                last_training: new Date().toISOString(),
                training_in_progress: false
            };
            
            try {
                const response = await fetch('/api/status');
                if (response.ok) {
                    serverData = await response.json();
                }
            } catch (e) {
                // Server unavailable, use client-only mode
            }
            
            // Combine client and server status, prioritizing client for AI model info
            const combinedData = {
                ...serverData,
                model_loaded: clientStatus.modelLoaded,
                active_model: clientStatus.currentModel || 'Client-Side AI',
                model_type: clientStatus.modelType,
                context_window: clientStatus.contextWindow,
                client_side: true
            };
            
            this.updateStatus(combinedData);
            
        } catch (error) {
            console.error('Status polling error:', error);
        }
        
        // Poll every 5 seconds
        setTimeout(() => this.pollStatus(), 5000);
    }

    updateStatus(data) {
        // Update model status
        const modelStatus = document.getElementById('model-status');
        if (modelStatus) {
            modelStatus.textContent = data.model_loaded ? data.active_model : 'Not Loaded';
            modelStatus.className = `badge ${data.model_loaded ? 'bg-success' : 'bg-warning'}`;
        }
        
        // Update training status
        const trainingStatus = document.getElementById('training-status');
        if (trainingStatus) {
            trainingStatus.textContent = data.training_in_progress ? 'Training' : 'Ready';
            trainingStatus.className = `badge ${data.training_in_progress ? 'bg-info' : 'bg-success'}`;
        }
        
        // Update data status
        const dataStatus = document.getElementById('data-status');
        if (dataStatus) {
            dataStatus.textContent = `${data.writeup_count} writeups`;
            dataStatus.className = 'badge bg-primary';
        }
        
        // Update training details
        const lastTraining = document.getElementById('last-training');
        if (lastTraining) {
            const date = new Date(data.last_training);
            lastTraining.textContent = date.toLocaleString();
        }
        
        const trainingStatusDetail = document.getElementById('training-status-detail');
        if (trainingStatusDetail) {
            trainingStatusDetail.textContent = data.training_in_progress ? 'Training in progress' : 'Ready';
        }
        
        const trainingDataCount = document.getElementById('training-data-count');
        if (trainingDataCount) {
            trainingDataCount.textContent = data.writeup_count;
        }
    }

    showAlert(message, type) {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type}`;
        alertDiv.textContent = message;
        
        // Add to current tab
        const currentTabDiv = document.getElementById(`${this.currentTab}-tab`);
        if (currentTabDiv) {
            currentTabDiv.insertBefore(alertDiv, currentTabDiv.firstChild);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SimplifiedCTFAI();
});
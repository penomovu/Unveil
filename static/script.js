/**
 * CTF AI System Frontend JavaScript
 * Handles user interactions, API calls, and real-time updates
 */

class CTFAIApp {
    constructor() {
        this.currentTab = 'chat';
        this.statusUpdateInterval = null;
        this.chatEnabled = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeFeatherIcons();
        this.updateSystemStatus();
        this.startStatusUpdates();
        this.loadDataSources();
        this.checkChatAvailability();
    }

    initializeFeatherIcons() {
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('[data-tab]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab(link.dataset.tab);
            });
        });

        // Chat functionality
        this.setupChatListeners();
        
        // Data collection
        this.setupDataCollectionListeners();
        
        // Training
        this.setupTrainingListeners();
        
        // Evaluation
        this.setupEvaluationListeners();
        
        // Settings
        this.setupSettingsListeners();
    }

    setupChatListeners() {
        const chatInput = document.getElementById('chat-input');
        const sendButton = document.getElementById('send-button');
        const clearButton = document.getElementById('clear-chat');

        if (chatInput && sendButton) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            sendButton.addEventListener('click', () => this.sendMessage());
        }

        if (clearButton) {
            clearButton.addEventListener('click', () => this.clearChat());
        }
    }

    setupDataCollectionListeners() {
        const startCollectionBtn = document.getElementById('start-collection');
        const addSourceBtn = document.getElementById('add-source-btn');
        const saveSourceBtn = document.getElementById('save-source');

        if (startCollectionBtn) {
            startCollectionBtn.addEventListener('click', () => this.startDataCollection());
        }

        if (addSourceBtn) {
            addSourceBtn.addEventListener('click', () => this.showAddSourceModal());
        }

        if (saveSourceBtn) {
            saveSourceBtn.addEventListener('click', () => this.addDataSource());
        }
    }

    setupTrainingListeners() {
        const startTrainingBtn = document.getElementById('start-training');
        const loadModelBtn = document.getElementById('load-model');

        if (startTrainingBtn) {
            startTrainingBtn.addEventListener('click', () => this.startTraining());
        }

        if (loadModelBtn) {
            loadModelBtn.addEventListener('click', () => this.loadExistingModel());
        }
    }

    setupEvaluationListeners() {
        const startEvaluationBtn = document.getElementById('start-evaluation');

        if (startEvaluationBtn) {
            startEvaluationBtn.addEventListener('click', () => this.startEvaluation());
        }
    }

    setupSettingsListeners() {
        const refreshStatusBtn = document.getElementById('refresh-status');
        const viewLogsBtn = document.getElementById('view-logs');
        const resetSystemBtn = document.getElementById('reset-system');

        if (refreshStatusBtn) {
            refreshStatusBtn.addEventListener('click', () => this.updateSystemStatus());
        }

        if (viewLogsBtn) {
            viewLogsBtn.addEventListener('click', () => this.viewLogs());
        }

        if (resetSystemBtn) {
            resetSystemBtn.addEventListener('click', () => this.resetSystem());
        }
    }

    switchTab(tabName) {
        // Update navigation
        document.querySelectorAll('[data-tab]').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Show tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');

        this.currentTab = tabName;
        this.initializeFeatherIcons();
    }

    async updateSystemStatus() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();

            // Update status indicators
            this.updateStatusBadge('model-status', status.model_loaded ? 'Loaded' : 'Not Loaded', 
                                 status.model_loaded ? 'success' : 'secondary');
            
            this.updateStatusBadge('data-status', status.collected_writeups > 0 ? `${status.collected_writeups} writeups` : 'No Data',
                                 status.collected_writeups > 0 ? 'info' : 'secondary');
            
            this.updateStatusBadge('training-status', this.capitalizeFirst(status.training_status), 
                                 this.getStatusColor(status.training_status));

            // Update detailed status displays
            this.updateDetailedStatus(status);
            
            // Update chat availability
            this.updateChatAvailability(status.model_loaded);

        } catch (error) {
            console.error('Failed to update system status:', error);
            this.showNotification('Failed to update system status', 'error');
        }
    }

    updateStatusBadge(elementId, text, colorClass) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = text;
            element.className = `badge bg-${colorClass}`;
        }
    }

    updateDetailedStatus(status) {
        // Training tab status
        const trainingStatusDisplay = document.getElementById('training-status-display');
        if (trainingStatusDisplay) {
            trainingStatusDisplay.textContent = this.capitalizeFirst(status.training_status);
            trainingStatusDisplay.className = `badge bg-${this.getStatusColor(status.training_status)}`;
        }

        const lastTraining = document.getElementById('last-training');
        if (lastTraining) {
            lastTraining.textContent = status.last_training_time || 'Never';
        }

        const modelLoaded = document.getElementById('model-loaded');
        if (modelLoaded) {
            modelLoaded.textContent = status.model_loaded ? 'Yes' : 'No';
            modelLoaded.className = `badge bg-${status.model_loaded ? 'success' : 'secondary'}`;
        }

        // Data collection status
        const collectionStatus = document.getElementById('collection-status');
        if (collectionStatus) {
            collectionStatus.textContent = this.capitalizeFirst(status.data_collection_status);
            collectionStatus.className = `badge bg-${this.getStatusColor(status.data_collection_status)}`;
        }

        const writeupsCount = document.getElementById('writeups-count');
        if (writeupsCount) {
            writeupsCount.textContent = status.collected_writeups || 0;
        }

        const lastCollection = document.getElementById('last-collection');
        if (lastCollection) {
            lastCollection.textContent = status.last_collection_time || 'Never';
        }

        // Update training button state
        const startTrainingBtn = document.getElementById('start-training');
        if (startTrainingBtn) {
            startTrainingBtn.disabled = status.collected_writeups === 0 || status.training_status === 'running';
        }

        // Update evaluation button state
        const startEvaluationBtn = document.getElementById('start-evaluation');
        if (startEvaluationBtn) {
            startEvaluationBtn.disabled = !status.model_loaded;
        }
    }

    updateChatAvailability(modelLoaded) {
        const chatInput = document.getElementById('chat-input');
        const sendButton = document.getElementById('send-button');

        if (chatInput && sendButton) {
            chatInput.disabled = !modelLoaded;
            sendButton.disabled = !modelLoaded;
            
            if (modelLoaded) {
                chatInput.placeholder = "Ask about CTF challenges, vulnerabilities, tools...";
                this.chatEnabled = true;
            } else {
                chatInput.placeholder = "Train or load a model to start chatting...";
                this.chatEnabled = false;
            }
        }
    }

    checkChatAvailability() {
        this.updateSystemStatus();
    }

    getStatusColor(status) {
        const colors = {
            'idle': 'secondary',
            'running': 'warning',
            'completed': 'success',
            'failed': 'danger'
        };
        return colors[status] || 'secondary';
    }

    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    startStatusUpdates() {
        if (this.statusUpdateInterval) {
            clearInterval(this.statusUpdateInterval);
        }
        this.statusUpdateInterval = setInterval(() => {
            this.updateSystemStatus();
        }, 5000); // Update every 5 seconds
    }

    // Chat functionality
    async sendMessage() {
        if (!this.chatEnabled) {
            this.showNotification('Please train or load a model first', 'warning');
            return;
        }

        const chatInput = document.getElementById('chat-input');
        const message = chatInput.value.trim();

        if (!message) return;

        // Add user message to chat
        this.addChatMessage(message, 'user');
        chatInput.value = '';

        // Show typing indicator
        const typingId = this.addTypingIndicator();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message }),
            });

            const result = await response.json();

            // Remove typing indicator
            this.removeTypingIndicator(typingId);

            if (response.ok) {
                this.addChatMessage(result.response, 'bot');
            } else {
                this.addChatMessage('Sorry, I encountered an error processing your message.', 'bot');
                this.showNotification(result.error || 'Chat error', 'error');
            }

        } catch (error) {
            this.removeTypingIndicator(typingId);
            this.addChatMessage('Sorry, I couldn\'t connect to the server.', 'bot');
            console.error('Chat error:', error);
        }
    }

    addChatMessage(message, sender) {
        const chatMessages = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;

        const timestamp = new Date().toLocaleTimeString();
        
        messageDiv.innerHTML = `
            <div class="message-content">
                ${sender === 'bot' ? '<strong>CTF AI:</strong> ' : ''}${this.escapeHtml(message)}
            </div>
            <div class="message-time">${timestamp}</div>
        `;

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    addTypingIndicator() {
        const chatMessages = document.getElementById('chat-messages');
        const typingDiv = document.createElement('div');
        const typingId = 'typing-' + Date.now();
        
        typingDiv.id = typingId;
        typingDiv.className = 'message bot-message';
        typingDiv.innerHTML = `
            <div class="message-content">
                <strong>CTF AI:</strong> <span class="typing-dots">Thinking<span>.</span><span>.</span><span>.</span></span>
            </div>
        `;

        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return typingId;
    }

    removeTypingIndicator(typingId) {
        const typingDiv = document.getElementById(typingId);
        if (typingDiv) {
            typingDiv.remove();
        }
    }

    clearChat() {
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.innerHTML = `
            <div class="message bot-message">
                <div class="message-content">
                    <strong>CTF AI:</strong> Hello! I'm your cybersecurity CTF assistant. I can help you with questions about CTF challenges, security techniques, tools, and exploitation methods. What would you like to know?
                </div>
                <div class="message-time">System</div>
            </div>
        `;
    }

    // Data collection functionality
    async loadDataSources() {
        try {
            const response = await fetch('/api/data-sources');
            const sources = await response.json();
            this.displayDataSources(sources);
        } catch (error) {
            console.error('Failed to load data sources:', error);
        }
    }

    displayDataSources(sources) {
        const sourcesList = document.getElementById('sources-list');
        if (!sourcesList) return;

        if (!sources || sources.length === 0) {
            sourcesList.innerHTML = '<p class="text-muted">No data sources configured.</p>';
            return;
        }

        sourcesList.innerHTML = sources.map(source => `
            <div class="source-item">
                <div class="source-header">
                    <span class="source-name">${this.escapeHtml(source.name)}</span>
                    <span class="source-type">${source.type}</span>
                </div>
                <div class="source-url">${this.escapeHtml(source.url)}</div>
                <small class="text-muted">Added: ${source.added_date || 'Unknown'}</small>
            </div>
        `).join('');
    }

    showAddSourceModal() {
        const modal = new bootstrap.Modal(document.getElementById('addSourceModal'));
        modal.show();
    }

    async addDataSource() {
        const url = document.getElementById('source-url').value.trim();
        const type = document.getElementById('source-type').value;
        const name = document.getElementById('source-name').value.trim();

        if (!url || !type) {
            this.showNotification('Please fill in all required fields', 'warning');
            return;
        }

        try {
            const response = await fetch('/api/add-source', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url, type, name }),
            });

            const result = await response.json();

            if (response.ok) {
                this.showNotification('Data source added successfully', 'success');
                bootstrap.Modal.getInstance(document.getElementById('addSourceModal')).hide();
                this.loadDataSources();
                
                // Clear form
                document.getElementById('add-source-form').reset();
            } else {
                this.showNotification(result.error || 'Failed to add source', 'error');
            }

        } catch (error) {
            console.error('Error adding source:', error);
            this.showNotification('Failed to add source', 'error');
        }
    }

    async startDataCollection() {
        const button = document.getElementById('start-collection');
        const originalText = button.innerHTML;
        
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Starting...';

        try {
            const response = await fetch('/api/collect-data', {
                method: 'POST',
            });

            const result = await response.json();

            if (response.ok) {
                this.showNotification('Data collection started', 'success');
                this.showCollectionProgress();
            } else {
                this.showNotification(result.error || 'Failed to start collection', 'error');
            }

        } catch (error) {
            console.error('Collection error:', error);
            this.showNotification('Failed to start collection', 'error');
        } finally {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }

    showCollectionProgress() {
        const progressDiv = document.getElementById('collection-progress');
        if (progressDiv) {
            progressDiv.style.display = 'block';
            const progressBar = progressDiv.querySelector('.progress-bar');
            progressBar.style.width = '0%';
            
            // Simulate progress
            let progress = 0;
            const interval = setInterval(() => {
                progress += 5;
                progressBar.style.width = `${Math.min(progress, 90)}%`;
                
                if (progress >= 100) {
                    clearInterval(interval);
                    progressDiv.style.display = 'none';
                }
            }, 1000);
        }
    }

    // Training functionality
    async startTraining() {
        const button = document.getElementById('start-training');
        const originalText = button.innerHTML;
        
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Starting Training...';

        try {
            const response = await fetch('/api/train-model', {
                method: 'POST',
            });

            const result = await response.json();

            if (response.ok) {
                this.showNotification('Model training started', 'success');
                this.showTrainingProgress();
            } else {
                this.showNotification(result.error || 'Failed to start training', 'error');
            }

        } catch (error) {
            console.error('Training error:', error);
            this.showNotification('Failed to start training', 'error');
        } finally {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }

    async loadExistingModel() {
        const button = document.getElementById('load-model');
        const originalText = button.innerHTML;
        
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';

        try {
            const response = await fetch('/api/load-model', {
                method: 'POST',
            });

            const result = await response.json();

            if (response.ok) {
                this.showNotification('Model loaded successfully', 'success');
                this.updateSystemStatus();
            } else {
                this.showNotification(result.error || 'Failed to load model', 'error');
            }

        } catch (error) {
            console.error('Load model error:', error);
            this.showNotification('Failed to load model', 'error');
        } finally {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }

    showTrainingProgress() {
        const progressDiv = document.getElementById('training-progress');
        if (progressDiv) {
            progressDiv.style.display = 'block';
            const progressBar = progressDiv.querySelector('.progress-bar');
            progressBar.style.width = '0%';
            
            // Simulate training progress
            let progress = 0;
            const interval = setInterval(() => {
                progress += 2;
                progressBar.style.width = `${Math.min(progress, 95)}%`;
                
                if (progress >= 100) {
                    clearInterval(interval);
                    progressDiv.style.display = 'none';
                }
            }, 2000);
        }
    }

    // Evaluation functionality
    async startEvaluation() {
        const button = document.getElementById('start-evaluation');
        const originalText = button.innerHTML;
        
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Evaluating...';

        try {
            const response = await fetch('/api/evaluate', {
                method: 'POST',
            });

            const result = await response.json();

            if (response.ok) {
                this.showNotification('Evaluation completed', 'success');
                this.displayEvaluationResults(result);
            } else {
                this.showNotification(result.error || 'Evaluation failed', 'error');
            }

        } catch (error) {
            console.error('Evaluation error:', error);
            this.showNotification('Evaluation failed', 'error');
        } finally {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    }

    displayEvaluationResults(results) {
        const resultsDiv = document.getElementById('evaluation-results');
        if (!resultsDiv) return;

        const overall = results.overall_performance || {};
        const categories = results.category_performance || {};

        resultsDiv.innerHTML = `
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="evaluation-metric">
                        <span class="metric-value">${(overall.average_score * 100).toFixed(1)}%</span>
                        <span class="metric-label">Overall Score</span>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="evaluation-metric">
                        <span class="metric-value">${overall.total_questions || 0}</span>
                        <span class="metric-label">Questions Tested</span>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="evaluation-metric">
                        <span class="metric-value">${(results.keyword_coverage?.overall_coverage * 100 || 0).toFixed(1)}%</span>
                        <span class="metric-label">Keyword Coverage</span>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="evaluation-metric">
                        <span class="metric-value">${(results.response_quality?.completeness_rate * 100 || 0).toFixed(1)}%</span>
                        <span class="metric-label">Completeness</span>
                    </div>
                </div>
            </div>
            
            <h5>Category Performance</h5>
            <div class="category-performance">
                ${Object.entries(categories).map(([category, perf]) => `
                    <div class="category-card">
                        <div class="category-title">${category}</div>
                        <div class="category-score" style="color: ${this.getScoreColor(perf.average_score)}">${(perf.average_score * 100).toFixed(1)}%</div>
                        <div class="category-level badge ${this.getLevelBadgeClass(perf.strength_level)}">${perf.strength_level}</div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    getScoreColor(score) {
        if (score >= 0.8) return '#198754';
        if (score >= 0.6) return '#fd7e14';
        if (score >= 0.4) return '#ffc107';
        return '#dc3545';
    }

    getLevelBadgeClass(level) {
        const classes = {
            'Excellent': 'bg-success',
            'Good': 'bg-primary',
            'Fair': 'bg-warning',
            'Poor': 'bg-danger',
            'Very Poor': 'bg-danger'
        };
        return classes[level] || 'bg-secondary';
    }

    // Settings functionality
    viewLogs() {
        this.showNotification('Log viewing not implemented yet', 'info');
    }

    resetSystem() {
        if (confirm('Are you sure you want to reset the system? This will clear all data and models.')) {
            this.showNotification('System reset not implemented yet', 'info');
        }
    }

    // Utility functions
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${this.getBootstrapAlertClass(type)} alert-dismissible fade show`;
        notification.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    getBootstrapAlertClass(type) {
        const classes = {
            'success': 'success',
            'error': 'danger',
            'warning': 'warning',
            'info': 'info'
        };
        return classes[type] || 'info';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatTimestamp(timestamp) {
        if (!timestamp) return 'Never';
        return new Date(timestamp).toLocaleString();
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.ctfAI = new CTFAIApp();
});

// Add some CSS for typing animation
const style = document.createElement('style');
style.textContent = `
    .typing-dots span {
        animation: typing 1.4s infinite;
        animation-fill-mode: both;
    }
    
    .typing-dots span:nth-child(1) { animation-delay: 0.2s; }
    .typing-dots span:nth-child(2) { animation-delay: 0.4s; }
    .typing-dots span:nth-child(3) { animation-delay: 0.6s; }
    
    @keyframes typing {
        0%, 60%, 100% { opacity: 0; }
        30% { opacity: 1; }
    }
`;
document.head.appendChild(style);

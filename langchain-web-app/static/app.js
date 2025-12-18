// LangChain Studio - Frontend Application
class LangChainApp {
    constructor() {
        this.currentView = 'chat';
        this.messages = [];
        this.models = [];
        this.init();
    }

    init() {
        this.setupSession();
        this.setupEventListeners();
        this.setupUploadHandlers();
        this.setupAgentHandler();
        this.loadModels();
        this.loadHistory(); // Load previous chat
        this.autoResizeTextarea();
    }

    setupSession() {
        let sessionId = localStorage.getItem('chat_session_id');
        if (!sessionId) {
            sessionId = 'sess_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('chat_session_id', sessionId);
        }
        this.sessionId = sessionId;
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const view = e.currentTarget.dataset.view;
                this.switchView(view);
            });
        });

        // Chat functionality
        const sendButton = document.getElementById('send-button');
        const messageInput = document.getElementById('message-input');
        const clearButton = document.getElementById('clear-chat');

        sendButton.addEventListener('click', () => this.sendMessage());
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        clearButton.addEventListener('click', () => this.clearChat());

        // Auto-resize textarea
        messageInput.addEventListener('input', () => {
            this.autoResizeTextarea();
        });
    }

    setupUploadHandlers() {
        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');

        if (!dropZone || !fileInput) return;

        // Drag and drop events
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'));
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'));
        });

        dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            this.handleFiles(files);
        });

        fileInput.addEventListener('change', () => {
            this.handleFiles(fileInput.files);
        });
    }

    setupAgentHandler() {
        const runBtn = document.getElementById('run-agent-btn');
        const goalInput = document.getElementById('agent-goal');
        const resultDiv = document.getElementById('agent-result');
        const resultContent = resultDiv ? resultDiv.querySelector('.result-content') : null;

        if (!runBtn || !goalInput) return;

        runBtn.addEventListener('click', async () => {
            const goal = goalInput.value.trim();
            if (!goal) return;

            // Loading state
            runBtn.disabled = true;
            runBtn.textContent = 'Agent is thinking... (this may take a moment)';
            resultDiv.classList.add('hidden');

            try {
                const response = await fetch('/api/agent', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ goal })
                });

                const data = await response.json();

                if (!response.ok) throw new Error(data.error || 'Agent failed');

                // Show Result
                resultContent.textContent = data.output;
                resultDiv.classList.remove('hidden');

            } catch (error) {
                console.error('Agent Error:', error);
                resultContent.textContent = `❌ ${error.message}`;
                resultContent.style.color = 'var(--danger-color)';
                resultDiv.classList.remove('hidden');
            } finally {
                runBtn.disabled = false;
                runBtn.textContent = 'Execute Agent';
            }
        });
    }

    handleFiles(files) {
        if (files.length > 0) {
            this.uploadFile(files[0]);
        }
    }

    async uploadFile(file) {
        const statusDiv = document.getElementById('upload-status');
        const progressBar = statusDiv.querySelector('.progress-fill');
        const statusText = statusDiv.querySelector('.status-text');

        statusDiv.classList.remove('hidden');
        progressBar.style.width = '0%';
        statusText.textContent = `Uploading ${file.name}...`;

        const formData = new FormData();
        formData.append('file', file);

        try {
            // Simulated progress
            progressBar.style.width = '50%';

            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error('Upload failed');

            const result = await response.json();

            progressBar.style.width = '100%';
            statusText.textContent = `✅ ${result.message} (${result.chunks} chunks)`;
            statusText.style.color = 'var(--success-color)';

            // Revert status after delay
            setTimeout(() => {
                statusDiv.classList.add('hidden');
                statusText.style.color = '';
                // Optional: switch to chat view automatically?
                // this.switchView('chat'); 
            }, 3000);

        } catch (error) {
            console.error('Upload Error:', error);
            statusText.textContent = '❌ Upload failed. Please try again.';
            statusText.style.color = 'var(--danger-color)';
            progressBar.style.background = 'var(--danger-color)';
        }
    }

    switchView(viewName) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-view="${viewName}"]`).classList.add('active');

        // Update views
        document.querySelectorAll('.view').forEach(view => {
            view.classList.remove('active');
        });
        document.getElementById(`${viewName}-view`).classList.add('active');

        this.currentView = viewName;

        // Load view-specific data
        if (viewName === 'models' && this.models.length === 0) {
            this.loadModels();
        }
    }

    async sendMessage() {
        const input = document.getElementById('message-input');
        const message = input.value.trim();

        if (!message) return;

        // Clear input
        input.value = '';
        this.autoResizeTextarea();

        // Add user message to UI
        this.addMessage('user', message);

        // Disable send button
        const sendButton = document.getElementById('send-button');
        sendButton.disabled = true;

        // Create Assistant Message Placeholder
        const aiMessageDiv = this.addMessage('assistant', '...');
        const aiContent = aiMessageDiv.querySelector('.message-content');
        let fullResponse = '';

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Session-ID': this.sessionId
                },
                body: JSON.stringify({ message })
            });

            if (!response.ok) throw new Error('Network response form was not ok');

            // Handle sources header
            const sourcesHeader = response.headers.get('X-Sources');
            const sources = sourcesHeader ? JSON.parse(sourcesHeader) : [];

            // Clear '...' loading state
            aiContent.textContent = '';

            // Read the stream
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                fullResponse += chunk;
                // Basic markdown to HTML (you might want a library like marked.js)
                aiContent.innerHTML = fullResponse.replace(/\n/g, '<br>');
                this.scrollToBottom();
            }

            // Append sources if available
            if (sources && sources.length > 0) {
                const sourcesHtml = `
                    <div class="sources-list" style="margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);">
                        <small style="color: var(--text-tertiary);">Sources: ${sources.join(', ')}</small>
                    </div>
                `;
                aiContent.insertAdjacentHTML('beforeend', sourcesHtml);
            }

        } catch (error) {
            console.error('Chat Error:', error);
            aiContent.textContent = '❌ Error: Failed to get response.';
            aiContent.style.color = 'var(--danger-color)';
        } finally {
            sendButton.disabled = false;
            input.focus();
        }
    }

    addMessage(role, text) {
        const messagesContainer = document.getElementById('messages');

        // Remove welcome message if it exists
        const welcomeMessage = messagesContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = role === 'user' ? '👤' : '🦜';

        const content = document.createElement('div');
        content.className = 'message-content';

        // Direct text textContent if not '...' (placeholder)
        if (text === '...') {
            // Placeholder
            content.innerHTML = '<span class="typing-indicator">...</span>';
        } else {
            content.textContent = text;
        }

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);

        messagesContainer.appendChild(messageDiv);

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Store message
        this.messages.push({ role, text, timestamp: new Date() });

        return messageDiv; // Vital for streaming updates

    }

    async loadHistory() {
        try {
            const response = await fetch('/api/history', {
                headers: { 'X-Session-ID': this.sessionId }
            });
            if (response.ok) {
                const history = await response.json();
                if (history.length > 0) {
                    // Clear welcome message if history exists
                    const messagesContainer = document.getElementById('messages');
                    const welcomeMessage = messagesContainer.querySelector('.welcome-message');
                    if (welcomeMessage) welcomeMessage.remove();

                    history.forEach(msg => {
                        this.addMessage(msg.role, msg.content);
                    });
                }
            }
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    }

    clearChat() {
        const messagesContainer = document.getElementById('messages');
        messagesContainer.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">🦜</div>
                <h3>Welcome to LangChain Studio</h3>
                <p>Start a conversation to explore AI-powered applications</p>
            </div>
        `;
        this.messages = [];
        // Optional: Clear on backend too if we implemented that
    }

    async loadModels() {
        const modelsGrid = document.getElementById('models-grid');
        modelsGrid.innerHTML = '<div class="loading">Loading models...</div>';

        try {
            const response = await fetch('/api/models');
            if (!response.ok) {
                throw new Error('Failed to load models');
            }

            this.models = await response.json();
            this.renderModels();

            // Update model selector
            const modelSelector = document.getElementById('model-selector');
            modelSelector.innerHTML = '<option value="demo">Demo Mode</option>';
            this.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = `${model.name} (${model.provider})`;
                modelSelector.appendChild(option);
            });

        } catch (error) {
            console.error('Error loading models:', error);
            modelsGrid.innerHTML = '<div class="loading">Failed to load models</div>';
        }
    }

    renderModels() {
        const modelsGrid = document.getElementById('models-grid');
        modelsGrid.innerHTML = '';

        this.models.forEach(model => {
            const card = document.createElement('div');
            card.className = 'model-card';
            card.innerHTML = `
                <h3>${model.name}</h3>
                <div class="provider">${model.provider}</div>
                <div class="badge">Available</div>
            `;
            modelsGrid.appendChild(card);
        });
    }

    autoResizeTextarea() {
        const textarea = document.getElementById('message-input');
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }

    async checkHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            console.log('Health check:', data);
            return data.status === 'healthy';
        } catch (error) {
            console.error('Health check failed:', error);
            return false;
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Main App
    window.app = new LangChainApp();
    // Check health on startup
    window.app.checkHealth().then(healthy => {
        if (healthy) {
            console.log('✓ LangChain Studio is ready');
        } else {
            console.warn('⚠ Backend connection issue');
        }
    });
});



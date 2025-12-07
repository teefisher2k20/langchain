// LangChain Studio - Frontend Application
class LangChainApp {
    constructor() {
        this.currentView = 'chat';
        this.messages = [];
        this.models = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadModels();
        this.autoResizeTextarea();
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

        try {
            // Send to backend
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message }),
            });

            if (!response.ok) {
                throw new Error('Failed to get response');
            }

            const data = await response.json();

            // Add assistant message
            this.addMessage('assistant', data.message);

        } catch (error) {
            console.error('Error:', error);
            this.addMessage('assistant', '❌ Sorry, there was an error processing your request. Please try again.');
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

        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        messageText.textContent = text;

        const time = document.createElement('div');
        time.className = 'message-time';
        time.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        content.appendChild(messageText);
        content.appendChild(time);

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);

        messagesContainer.appendChild(messageDiv);

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Store message
        this.messages.push({ role, text, timestamp: new Date() });
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

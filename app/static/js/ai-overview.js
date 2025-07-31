class AIOverview {
    constructor() {
        this.serviceConfigured = window.serviceConfigured || false;
        this.initializeElements();
        this.bindEvents();
        this.checkServiceStatus();
    }

    initializeElements() {
        this.searchInput = document.getElementById('searchQuery');
        this.generateBtn = document.getElementById('generateBtn');
        this.charCount = document.getElementById('charCount');
        this.loadingState = document.getElementById('loadingState');
        this.overviewResult = document.getElementById('overviewResult');
        this.overviewTemplate = document.getElementById('overviewTemplate');
        this.sourceTemplate = document.getElementById('sourceTemplate');
    }

    async checkServiceStatus() {
        if (!this.serviceConfigured) {
            return;
        }

        try {
            const response = await fetch('/ai-overview/api/service-status');
            const data = await response.json();

            if (!data.configured) {
                this.serviceConfigured = false;
                this.disableService('Service configuration incomplete');
            }
        } catch (error) {
            console.error('Error checking service status:', error);
            this.disableService('Unable to check service status');
        }
    }

    disableService(message) {
        this.searchInput.disabled = true;
        this.generateBtn.disabled = true;
        this.showError(message);
    }

    bindEvents() {
        // Search input events
        this.searchInput.addEventListener('input', (e) => {
            this.updateCharCount();
            this.validateInput();
        });

        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !this.generateBtn.disabled) {
                this.generateOverview();
            }
        });

        // Generate button
        this.generateBtn.addEventListener('click', () => {
            this.generateOverview();
        });
    }

    updateCharCount() {
        const count = this.searchInput.value.length;
        this.charCount.textContent = count;

        if (count > 450) {
            this.charCount.className = 'text-red-500';
        } else if (count > 400) {
            this.charCount.className = 'text-yellow-500';
        } else {
            this.charCount.className = 'text-gray-500';
        }
    }

    validateInput() {
        if (!this.serviceConfigured) {
            return;
        }

        const query = this.searchInput.value.trim();
        const isValid = query.length >= 3 && query.length <= 500;

        this.generateBtn.disabled = !isValid;

        if (!isValid && query.length > 0) {
            if (query.length < 3) {
                this.showError('Query must be at least 3 characters long');
            } else if (query.length > 500) {
                this.showError('Query must be less than 500 characters');
            }
        } else {
            this.hideError();
        }
    }

    async generateOverview() {
        if (!this.serviceConfigured) {
            this.showError('AI Overview service is not configured');
            return;
        }

        const query = this.searchInput.value.trim();

        if (!query) {
            this.showError('Please enter a question');
            return;
        }

        try {
            this.showLoading();
            this.hideError();

            const response = await fetch('/ai-overview/api/generate-overview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query })
            });

            const data = await response.json();

            if (data.success) {
                this.displayOverview(data.data);
            } else {
                this.showError(data.error || 'Failed to generate overview');
            }

        } catch (error) {
            console.error('Error generating overview:', error);
            this.showError('Network error. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    displayOverview(overviewData) {
        // Clone template
        const template = this.overviewTemplate.content.cloneNode(true);

        // Fill in data
        template.getElementById('overviewQuery').textContent = overviewData.query;
        template.getElementById('overviewText').textContent = overviewData.overview_text;

        // Meta information
        const processingTime = overviewData.processing_time ?
            `${overviewData.processing_time.toFixed(1)}s` : 'N/A';
        const sourceCount = overviewData.sources_used ? overviewData.sources_used.length : 0;

        template.getElementById('overviewMeta').textContent =
            `Generated in ${processingTime} • ${sourceCount} sources`;

        // Add sources
        const sourcesList = template.getElementById('sourcesList');
        if (overviewData.sources_used && overviewData.sources_used.length > 0) {
            overviewData.sources_used.forEach(source => {
                const sourceElement = this.createSourceElement(source);
                sourcesList.appendChild(sourceElement);
            });
        }

        // Clear and show result
        this.overviewResult.innerHTML = '';
        this.overviewResult.appendChild(template);
        this.overviewResult.classList.remove('hidden');

        // Scroll to result
        this.overviewResult.scrollIntoView({ behavior: 'smooth' });
    }

    createSourceElement(source) {
        const template = this.sourceTemplate.content.cloneNode(true);

        const link = template.querySelector('.source-link');
        link.href = source.url;
        link.textContent = source.title;

        template.querySelector('.source-snippet').textContent = source.snippet;
        template.querySelector('.source-url').textContent = new URL(source.url).hostname;

        const status = template.querySelector('.source-status');
        if (source.content_extracted) {
            status.textContent = 'Content Used';
            status.className = 'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800';
        } else {
            status.textContent = 'Referenced';
            status.className = 'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800';
        }

        return template;
    }

    showLoading() {
        this.loadingState.classList.remove('hidden');
        this.overviewResult.classList.add('hidden');
        this.generateBtn.disabled = true;
        this.generateBtn.textContent = 'Generating...';
    }

    hideLoading() {
        this.loadingState.classList.add('hidden');
        if (this.serviceConfigured) {
            this.generateBtn.disabled = false;
        }
        this.generateBtn.textContent = 'Generate Overview';
    }

    showError(message) {
        // Create or update error message
        let errorDiv = document.getElementById('errorMessage');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'errorMessage';
            errorDiv.className = 'mt-2 p-3 bg-red-100 border border-red-400 text-red-700 rounded-md text-sm';
            this.searchInput.parentNode.appendChild(errorDiv);
        }
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
    }

    hideError() {
        const errorDiv = document.getElementById('errorMessage');
        if (errorDiv) {
            errorDiv.classList.add('hidden');
        }
    }
}

// Global function for loading previous overviews
async function loadOverview(overviewId) {
    try {
        const response = await fetch(`/ai-overview/api/overview/${overviewId}`);
        const data = await response.json();

        if (data.success) {
            const aiOverview = new AIOverview();
            aiOverview.displayOverview(data.data);

            // Update search input
            document.getElementById('searchQuery').value = data.data.query;
        }
    } catch (error) {
        console.error('Error loading overview:', error);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AIOverview();
});
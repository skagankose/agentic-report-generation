// Main application JavaScript for document generation UI

class DocumentGenerator {
    constructor() {
        this.socket = io();
        this.currentSessionId = null;
        this.progressSteps = [
            "Genel bölüm hazırlanıyor...",
            "Teknik analiz yapılıyor...",
            "Pazar analizi gerçekleştiriliyor...",
            "Maliyet analizi hesaplanıyor...",
            "Finansal analiz yapılıyor...",
            "Risk analizi değerlendiriliyor...",
            "Sonuçlar derleniyor...",
            "Rapor formatlanıyor..."
        ];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupSocketListeners();
        this.animateElements();
    }

    setupEventListeners() {
        // Form submission
        const form = document.getElementById('report-form');
        if (form) {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }

        // Textarea auto-resize
        const textarea = document.getElementById('topic');
        if (textarea) {
            textarea.addEventListener('input', this.autoResizeTextarea);
        }
    }

    setupSocketListeners() {
        // Connection events
        this.socket.on('connect', () => {
            console.log('Connected to server');
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
        });

        // Progress updates
        this.socket.on('progress_update', (data) => {
            this.updateProgress(data);
        });

        // Report completion
        this.socket.on('report_complete', (data) => {
            this.showCompletion(data);
        });

        // Error handling
        this.socket.on('error', (data) => {
            this.showError(data.message);
        });
    }

    async handleFormSubmit(e) {
        e.preventDefault();
        
        const topic = document.getElementById('topic').value.trim();
        if (!topic) {
            this.showToast('Lütfen bir konu giriniz.', 'warning');
            return;
        }

        // Disable form and show loading
        this.setLoadingState(true);
        this.showProgress();

        try {
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ topic: topic })
            });

            const data = await response.json();

            if (response.ok) {
                this.currentSessionId = data.session_id;

                // 1. Join the session room
                this.socket.emit('join_session', { session_id: this.currentSessionId });

                // 2. Immediately after, tell the server to start the generation.
                // This is safe because SocketIO messages are ordered. The server will
                // process 'join_session' before 'start_generation' for this client.
                this.socket.emit('start_generation', { session_id: this.currentSessionId });
                
                this.showToast('Rapor oluşturma işlemi başlatıldı...', 'success');
            } else {
                throw new Error(data.error || 'Bilinmeyen hata oluştu');
            }
        } catch (error) {
            this.showError(error.message);
            this.setLoadingState(false);
        }
    }

    updateProgress(data) {
        const progressBar = document.getElementById('progress-bar');
        const currentStep = document.getElementById('current-step');
        const stepInfo = document.getElementById('step-info');

        if (progressBar) {
            progressBar.style.width = `${data.progress}%`;
            progressBar.textContent = `${data.progress}%`;
            progressBar.setAttribute('aria-valuenow', data.progress);
        }

        if (currentStep) {
            currentStep.textContent = data.step;
        }

        if (stepInfo) {
            stepInfo.textContent = `Adım ${data.step_number} / ${data.total_steps}`;
        }

        // Update step indicators
        this.updateStepIndicators(data.step_number);

        // Animate progress bar
        if (progressBar) {
            progressBar.classList.add('pulse');
            setTimeout(() => {
                progressBar.classList.remove('pulse');
            }, 500);
        }
    }

    updateStepIndicators(currentStep) {
        const stepItems = document.querySelectorAll('.list-unstyled li');
        stepItems.forEach((item, index) => {
            const icon = item.querySelector('i');
            
            // First, reset all state classes
            item.classList.remove('step-completed', 'step-active', 'step-pending');
            
            if (index < currentStep - 1) {
                icon.className = 'fas fa-check-circle text-success me-2';
                item.classList.add('step-completed');
            } else if (index === currentStep - 1) {
                icon.className = 'fas fa-cog fa-spin text-primary me-2';
                item.classList.add('step-active');
            } else {
                icon.className = 'fas fa-circle text-muted me-2';
                item.classList.add('step-pending');
            }
        });
    }

    showProgress() {
        this.hideAllSections();
        const progressSection = document.getElementById('progress-section');
        if (progressSection) {
            progressSection.style.display = 'block';
            progressSection.classList.add('fade-in-up');
        }
    }

    showCompletion(data) {
        this.hideAllSections();
        const completionSection = document.getElementById('completion-section');
        const reportStats = document.getElementById('report-stats');
        const viewReportBtn = document.getElementById('view-report-btn');
        const downloadDocxBtn = document.getElementById('download-docx-btn');
        const downloadMdBtn = document.getElementById('download-md-btn');

        if (completionSection) {
            completionSection.style.display = 'block';
            completionSection.classList.add('fade-in-up');
        }

        if (reportStats) {
            reportStats.textContent = `${data.citations} kaynak kullanılarak ${data.length.toLocaleString()} karakter uzunluğunda rapor oluşturuldu.`;
        }

        if (viewReportBtn && this.currentSessionId) {
            viewReportBtn.href = `/report/${this.currentSessionId}`;
        }

        if (downloadDocxBtn && this.currentSessionId) {
            downloadDocxBtn.href = `/download/${this.currentSessionId}/docx`;
        }

        if (downloadMdBtn && this.currentSessionId) {
            downloadMdBtn.href = `/download/${this.currentSessionId}/md`;
        }

        this.setLoadingState(false);
        this.celebrateCompletion();
    }

    showError(message) {
        this.hideAllSections();
        const errorSection = document.getElementById('error-section');
        const errorMessage = document.getElementById('error-message');

        if (errorSection) {
            errorSection.style.display = 'block';
            errorSection.classList.add('fade-in-up');
        }

        if (errorMessage) {
            errorMessage.textContent = message;
        }

        this.setLoadingState(false);
        this.showToast('Rapor oluşturulurken hata oluştu', 'error');
    }

    hideAllSections() {
        const sections = [
            'input-section',
            'progress-section', 
            'completion-section',
            'error-section'
        ];

        sections.forEach(sectionId => {
            const section = document.getElementById(sectionId);
            if (section) {
                section.style.display = 'none';
                section.classList.remove('fade-in-up');
            }
        });
    }

    setLoadingState(loading) {
        const form = document.getElementById('report-form');
        const submitBtn = form ? form.querySelector('button[type="submit"]') : null;
        const textarea = document.getElementById('topic');

        if (loading) {
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>İşleniyor...';
            }
            if (textarea) {
                textarea.disabled = true;
            }
        } else {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-rocket me-2"></i>Rapor Oluştur';
            }
            if (textarea) {
                textarea.disabled = false;
            }
        }
    }

    autoResizeTextarea(e) {
        e.target.style.height = 'auto';
        e.target.style.height = e.target.scrollHeight + 'px';
    }

    showToast(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="fas fa-${this.getToastIcon(type)} me-2"></i>
                ${message}
            </div>
        `;

        // Add to page
        document.body.appendChild(toast);

        // Show with animation
        setTimeout(() => {
            toast.classList.add('show');
        }, 100);

        // Remove after delay
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 4000);
    }

    getToastIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    celebrateCompletion() {
        // Add confetti or celebration animation
        const completionIcon = document.querySelector('#completion-section .fa-check-circle');
        if (completionIcon) {
            completionIcon.classList.add('pulse');
            setTimeout(() => {
                completionIcon.classList.remove('pulse');
            }, 2000);
        }

        // Play success sound (if needed)
        // this.playSound('success');
    }

    animateElements() {
        // Add entrance animations to elements
        const cards = document.querySelectorAll('.card');
        cards.forEach((card, index) => {
            setTimeout(() => {
                card.classList.add('fade-in-up');
            }, index * 200);
        });
    }
}

// Global functions
function startNew() {
    window.location.reload();
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new DocumentGenerator();
});

// Add toast styles
const toastStyles = `
<style>
.toast-notification {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 9999;
    padding: 15px 20px;
    border-radius: 10px;
    color: white;
    font-weight: 600;
    transform: translateX(100%);
    transition: transform 0.3s ease;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    max-width: 400px;
    word-wrap: break-word;
}

.toast-notification.show {
    transform: translateX(0);
}

.toast-success {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.toast-error {
    background: linear-gradient(135deg, #fc466b 0%, #3f5efb 100%);
}

.toast-warning {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.toast-info {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.toast-content {
    display: flex;
    align-items: center;
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', toastStyles);
/**
 * WMC Gateway Scanner - Backend Authentication Version
 * Version: 3.0.0
 * Updated: 2025-08-20 17:25:00 UTC
 * 
 * Features:
 * - Backend authentication (no user login required)
 * - QR code scanning
 * - Automatic WMC authentication
 * - Mobile-responsive design
 */

class WMCGatewayScanner {
    constructor() {
        this.scanner = null;
        this.isScanning = false;
        this.authStatus = {
            authenticated: false,
            token_valid: false
        };
        
        this.init();
    }

    async init() {
        console.log('🚀 Initializing WMC Gateway Scanner v3.0.0 (Backend Auth)');
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Check service status and auto-authenticate
        await this.checkServiceStatus();
        
        // Initialize status checks
        this.startStatusChecks();
        
        console.log('✅ WMC Gateway Scanner initialized');
    }

    setupEventListeners() {
        // QR Scanner controls
        document.getElementById('start-scan-btn')?.addEventListener('click', () => this.startScanning());
        document.getElementById('stop-scan-btn')?.addEventListener('click', () => this.stopScanning());
        
        // Manual EUI input
        document.getElementById('lookup-btn')?.addEventListener('click', () => this.lookupGateway());
        document.getElementById('manual-eui')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.lookupGateway();
            }
        });
        
        // Error handling
        document.getElementById('clear-error-btn')?.addEventListener('click', () => this.clearError());
        
        // Update auth section for backend auth
        this.updateAuthSection();
    }

    updateAuthSection() {
        // Replace auth section with backend auth status
        const header = document.querySelector('.app-header');
        if (header) {
            const authSection = document.createElement('div');
            authSection.className = 'auth-section';
            authSection.innerHTML = `
                <div class="auth-status" id="auth-status">
                    <span class="auth-icon">🔐</span>
                    <span class="auth-text" id="auth-status-text">Backend Authentication</span>
                </div>
                <div class="auth-info">
                    <small>Automatic login with saved credentials</small>
                </div>
            `;
            header.appendChild(authSection);
        }
    }

    async checkServiceStatus() {
        try {
            // Check service health and authentication
            const response = await fetch('/health');
            const status = await response.json();
            
            console.log('📊 Service status:', status);
            
            this.authStatus = {
                authenticated: status.authentication?.authenticated || false,
                token_valid: status.authentication?.token_valid || false
            };
            
            this.updateServiceDisplay(status);
            
        } catch (error) {
            console.error('❌ Service status check failed:', error);
            this.updateServiceDisplay(null);
        }
    }

    updateServiceDisplay(status) {
        const authText = document.getElementById('auth-status-text');
        const wmcStatus = document.getElementById('wmc-status');
        
        if (status) {
            if (authText) {
                if (status.authentication?.authenticated) {
                    authText.textContent = '🟢 Authenticated';
                    authText.className = 'auth-text authenticated';
                } else {
                    authText.textContent = '🔄 Authenticating...';
                    authText.className = 'auth-text authenticating';
                }
            }
            
            if (wmcStatus) {
                this.updateWMCStatus(
                    status.wmc_api_status === 'connected' ? '🟢 WMC Connected' : '🔴 WMC Disconnected',
                    status.wmc_api_status === 'connected' ? 'success' : 'error'
                );
            }
        } else {
            if (authText) {
                authText.textContent = '❌ Service Error';
                authText.className = 'auth-text error';
            }
            if (wmcStatus) {
                this.updateWMCStatus('🔴 Service Error', 'error');
            }
        }
    }

    async startScanning() {
        if (this.isScanning) return;
        
        // Check authentication before allowing scan
        await this.checkServiceStatus();
        
        if (!this.authStatus.authenticated) {
            this.showError('Service is authenticating with WMC, please wait...');
            return;
        }
        
        try {
            console.log('📷 Starting QR code scanner...');
            
            const qrReader = document.getElementById('qr-reader');
            if (!qrReader) {
                throw new Error('QR reader element not found');
            }
            
            this.scanner = new Html5Qrcode("qr-reader");
            
            const config = {
                fps: 10,
                qrbox: { width: 250, height: 250 },
                aspectRatio: 1.0
            };
            
            await this.scanner.start(
                { facingMode: "environment" },
                config,
                (decodedText, decodedResult) => {
                    console.log('🎯 QR Code detected:', decodedText);
                    this.handleQRCodeResult(decodedText);
                },
                (errorMessage) => {
                    // Handle scan errors silently
                }
            );
            
            this.isScanning = true;
            this.updateScannerControls();
            this.updateCameraStatus('📷 Scanning...', 'success');
            
        } catch (error) {
            console.error('❌ Scanner start error:', error);
            this.showError(`Scanner error: ${error.message}`);
            this.updateCameraStatus('📱 Scanner error', 'error');
        }
    }

    async stopScanning() {
        if (!this.isScanning || !this.scanner) return;
        
        try {
            await this.scanner.stop();
            this.scanner = null;
            this.isScanning = false;
            this.updateScannerControls();
            this.updateCameraStatus('📱 Camera ready', 'ready');
            console.log('⏹️ Scanner stopped');
        } catch (error) {
            console.error('❌ Scanner stop error:', error);
        }
    }

    updateScannerControls() {
        const startBtn = document.getElementById('start-scan-btn');
        const stopBtn = document.getElementById('stop-scan-btn');
        
        if (startBtn && stopBtn) {
            if (this.isScanning) {
                startBtn.style.display = 'none';
                stopBtn.style.display = 'inline-block';
            } else {
                startBtn.style.display = 'inline-block';
                stopBtn.style.display = 'none';
            }
        }
    }

    handleQRCodeResult(qrText) {
        console.log('🔍 Processing QR code:', qrText);
        
        // Stop scanning
        this.stopScanning();
        
        // Extract Gateway EUI from QR code
        let gatewayEUI = this.extractGatewayEUI(qrText);
        
        if (gatewayEUI) {
            this.lookupGateway(gatewayEUI);
        } else {
            this.showError('Could not extract Gateway EUI from QR code');
        }
    }

    extractGatewayEUI(qrText) {
        // Try different patterns to extract Gateway EUI
        const patterns = [
            /([A-Fa-f0-9]{16})/,           // 16-character hex
            /([A-Fa-f0-9-:]{19,23})/,     // With separators
            /EUI[:\s]*([A-Fa-f0-9-:]+)/i, // "EUI: ..." format
            /ID[:\s]*([A-Fa-f0-9-:]+)/i   // "ID: ..." format
        ];
        
        for (const pattern of patterns) {
            const match = qrText.match(pattern);
            if (match) {
                return match[1].replace(/[-:]/g, '').toUpperCase();
            }
        }
        
        // If no pattern matches, assume the entire text is the EUI
        const cleaned = qrText.replace(/[-:\s]/g, '').toUpperCase();
        if (/^[A-F0-9]{8,16}$/.test(cleaned)) {
            return cleaned;
        }
        
        return null;
    }

    async lookupGateway(gatewayEUI = null) {
        const eui = gatewayEUI || document.getElementById('manual-eui')?.value?.trim();
        
        if (!eui) {
            this.showError('Please enter a Gateway EUI');
            return;
        }
        
        try {
            console.log('🔍 Looking up gateway:', eui);
            this.showStatus('Looking up gateway...', 'info');
            
            const response = await fetch(`/api/v1/gateways/lookup/${encodeURIComponent(eui)}?include_stats=true`);
            
            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            console.log('✅ Gateway lookup successful:', data);
            this.displayGatewayInfo(data);
            this.hideStatus();
            
        } catch (error) {
            console.error('❌ Gateway lookup error:', error);
            this.showError(`Gateway lookup failed: ${error.message}`);
        }
    }

    displayGatewayInfo(data) {
        const resultsSection = document.getElementById('results-section');
        const gatewayInfo = document.getElementById('gateway-info');
        
        if (!resultsSection || !gatewayInfo) return;
        
        const gateway = data.gateway;
        
        const html = `
            <div class="gateway-card">
                <div class="gateway-header">
                    <h3>${gateway.name || 'Unnamed Gateway'}</h3>
                    <span class="gateway-status ${gateway.status || 'unknown'}">${gateway.status || 'Unknown'}</span>
                </div>
                
                <div class="gateway-details">
                    <div class="detail-row">
                        <span class="label">EUI:</span>
                        <span class="value">${gateway.eui || data.clean_eui}</span>
                    </div>
                    
                    ${gateway.location ? `
                    <div class="detail-row">
                        <span class="label">Location:</span>
                        <span class="value">${gateway.location}</span>
                    </div>
                    ` : ''}
                    
                    ${gateway.model ? `
                    <div class="detail-row">
                        <span class="label">Model:</span>
                        <span class="value">${gateway.model}</span>
                    </div>
                    ` : ''}
                    
                    ${gateway.lastSeen ? `
                    <div class="detail-row">
                        <span class="label">Last Seen:</span>
                        <span class="value">${new Date(gateway.lastSeen).toLocaleString()}</span>
                    </div>
                    ` : ''}
                    
                    <div class="detail-row">
                        <span class="label">Source:</span>
                        <span class="value">WMC API (Backend Auth)</span>
                    </div>
                </div>
                
                <div class="gateway-actions">
                    <button class="btn btn-secondary" onclick="gatewayScanner.clearResults()">
                        🔄 New Search
                    </button>
                </div>
            </div>
        `;
        
        gatewayInfo.innerHTML = html;
        resultsSection.style.display = 'block';
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    clearResults() {
        const resultsSection = document.getElementById('results-section');
        if (resultsSection) {
            resultsSection.style.display = 'none';
        }
        
        // Clear manual input
        const manualInput = document.getElementById('manual-eui');
        if (manualInput) {
            manualInput.value = '';
        }
    }

    showStatus(message, type = 'info') {
        // Create or update status display
        let statusDiv = document.getElementById('app-status');
        if (!statusDiv) {
            statusDiv = document.createElement('div');
            statusDiv.id = 'app-status';
            statusDiv.className = 'app-status';
            document.body.appendChild(statusDiv);
        }
        
        statusDiv.textContent = message;
        statusDiv.className = `app-status ${type}`;
        statusDiv.style.display = 'block';
    }

    hideStatus() {
        const statusDiv = document.getElementById('app-status');
        if (statusDiv) {
            statusDiv.style.display = 'none';
        }
    }

    showError(message) {
        console.error('❌ Error:', message);
        
        const errorSection = document.getElementById('error-section');
        const errorMessage = document.getElementById('error-message');
        
        if (errorSection && errorMessage) {
            errorMessage.textContent = message;
            errorSection.style.display = 'block';
            errorSection.scrollIntoView({ behavior: 'smooth' });
        } else {
            alert(`Error: ${message}`);
        }
    }

    clearError() {
        const errorSection = document.getElementById('error-section');
        if (errorSection) {
            errorSection.style.display = 'none';
        }
    }

    updateCameraStatus(text, status) {
        const cameraStatus = document.getElementById('camera-status');
        if (cameraStatus) {
            const statusText = cameraStatus.querySelector('.status-text');
            const statusIcon = cameraStatus.querySelector('.status-icon');
            
            if (statusText) statusText.textContent = text;
            
            // Update status class
            cameraStatus.className = `status-item ${status}`;
        }
    }

    updateWMCStatus(text, status) {
        const wmcStatus = document.getElementById('wmc-status');
        if (wmcStatus) {
            const statusText = wmcStatus.querySelector('.status-text');
            
            if (statusText) statusText.textContent = text;
            
            // Update status class
            wmcStatus.className = `status-item ${status}`;
        }
    }

    startStatusChecks() {
        // Check service status every 30 seconds
        setInterval(async () => {
            await this.checkServiceStatus();
        }, 30000);
    }
}

// Initialize the scanner when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.gatewayScanner = new WMCGatewayScanner();
});

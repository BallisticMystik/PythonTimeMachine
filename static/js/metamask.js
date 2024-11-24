document.addEventListener('DOMContentLoaded', function() {
    const connectButton = document.getElementById('connectButton');
    
    async function checkConnection() {
        if (typeof window.ethereum !== 'undefined') {
            try {
                const accounts = await window.ethereum.request({ method: 'eth_accounts' });
                if (accounts.length > 0) {
                    connectButton.textContent = 'Go to Dashboard';
                    connectButton.onclick = () => window.location.href = '/dashboard';
                } else {
                    connectButton.textContent = 'Connect MetaMask';
                    connectButton.onclick = connectWallet;
                }
            } catch (error) {
                console.error('Failed to check MetaMask connection:', error);
            }
        } else {
            console.log('MetaMask is not installed');
            connectButton.textContent = 'Install MetaMask';
            connectButton.onclick = () => window.open('https://metamask.io/download.html', '_blank');
        }
    }
    
    async function connectWallet() {
        if (typeof window.ethereum !== 'undefined') {
            try {
                const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
                console.log('MetaMask connected successfully!');
                
                const response = await fetch('/connect_wallet', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ wallet_address: accounts[0] }),
                });
                
                if (response.ok) {
                    window.location.href = '/login';
                } else {
                    console.error('Failed to send wallet address to server');
                }
            } catch (error) {
                console.error('Failed to connect to MetaMask:', error);
            }
        }
    }
    
    checkConnection();
    
    if (window.ethereum) {
        window.ethereum.on('accountsChanged', checkConnection);
    }
    
    // Check connection status on page load
    if (connectButton.textContent === 'Go to Dashboard') {
        connectButton.onclick = () => window.location.href = '/dashboard';
    } else {
        connectButton.onclick = connectWallet;
    }
});
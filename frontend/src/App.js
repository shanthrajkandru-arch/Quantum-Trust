import React, { useState, useEffect } from 'react';
import axios from 'axios';

// Import local components
import Header from './components/Header';
import Footer from './components/Footer';

// --- API Configuration ---
const API_URL = 'http://localhost:5000';

// --- Main Application Component ---
function App() {
    // --- STATE MANAGEMENT ---
    const [activeView, setActiveView] = useState('generate');
    const [account, setAccount] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [message, setMessage] = useState({ text: '', type: '' });

    // Centralized state for all page data to prevent data loss on navigation
    const [pageData, setPageData] = useState({
        generate: { result: null },
        verify: { bitstring: '', result: null },
        encrypt: { bitstring: '', plaintext: '', ciphertext: '' },
        decrypt: { bitstring: '', ciphertext: '', decryptedText: '' }
    });

// --- FINAL & CORRECT useEffect Hook for Wallet Connection ---
useEffect(() => {
    // This function checks for an existing connection when the app loads.
    const checkWalletConnection = async () => {
        if (window.ethereum) {
            try {
                // Silently request accounts. If the user is already connected and
                // their wallet is unlocked, this will return their address.
                const accounts = await window.ethereum.request({ method: 'eth_accounts' });

                // If an account is found, set it in our state.
                if (accounts.length > 0) {
                    setAccount(accounts[0]);
                }
            } catch (error) {
                console.error("Could not fetch accounts:", error);
            }
        }
    };

    // This function handles what happens when the user switches accounts,
    // locks their wallet, or disconnects.
    const handleAccountsChanged = (accounts) => {
        // If the accounts array is empty, it means the user has locked or disconnected.
        // This will set the account to null and show the welcome screen.
        setAccount(accounts.length > 0 ? accounts[0] : null);
    };

    // This function handles the important case where the user changes the network.
    const handleChainChanged = () => {
        // The recommended practice is to reload the page to ensure the app's
        // state is consistent with the new chain.
        window.location.reload();
    };

    if (window.ethereum) {
        // Set up the listeners for wallet events.
        window.ethereum.on('accountsChanged', handleAccountsChanged);
        window.ethereum.on('chainChanged', handleChainChanged);
    }

    // Run the initial connection check.
    checkWalletConnection();

    // This is a cleanup function that runs when the component unmounts.
    // It's a React best practice to prevent memory leaks.
    return () => {
        if (window.ethereum) {
            window.ethereum.removeListener('accountsChanged', handleAccountsChanged);
            window.ethereum.removeListener('chainChanged', handleChainChanged);
        }
    };
}, []);

    // --- CORE HANDLERS ---
    const connectWallet = async () => {
        if (window.ethereum) {
            try {
                const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
                setAccount(accounts[0]);
            } catch (error) { setMessage({ text: 'Failed to connect wallet.', type: 'error' }); }
        } else {
            setMessage({ text: 'MetaMask is not installed. Please install it to use this app.', type: 'error' });
        }
    };
    
    const handleViewChange = (view) => {
        setMessage({ text: '', type: '' }); // Clear message on navigation
        setActiveView(view);
    };

    const handleGenerateKey = async () => {
        setIsLoading(true);
        setMessage({ text: '', type: '' });
        setPageData(prev => ({ ...prev, generate: { result: null } }));

        try {
            const response = await axios.post(`${API_URL}/api/generate`);
            const newKey = response.data;
            setPageData(prev => ({ ...prev, generate: { result: newKey } }));
            setMessage({ text: `Successfully generated new Key ID #${newKey.id}.`, type: 'success' });
        } catch (error) {
            const errorMsg = error.response?.data?.error || 'Failed to generate key.';
            setMessage({ text: errorMsg, type: 'error' });
        } finally {
            setIsLoading(false);
        }
    };
    
    // --- RENDER LOGIC ---
    if (!account) {
        return (
            <div className="welcome-container">
                <Header />
                <div className="card">
                    <h2>Connect Your Wallet</h2>
                    <p>Please connect your MetaMask wallet to interact with the QuantumTrust dApp.</p>
                    <button className="button" onClick={connectWallet}>Connect Wallet</button>
                    {message.text && <p className={`message ${message.type}`}>{message.text}</p>}
                </div>
                <Footer />
            </div>
        );
    }

    return (
        <div className="App">
            <Header account={account} />
            <Navigation activeView={activeView} setActiveView={handleViewChange} />

            <main className="main-content">
                {message.text && <p className={`message ${message.type}`}>{message.text}</p>}

                {activeView === 'generate' && <GenerateView isLoading={isLoading} handleGenerateKey={handleGenerateKey} result={pageData.generate.result} />}
                {activeView === 'verify' && <VerifyView setMessage={setMessage} pageData={pageData} setPageData={setPageData} />}
                {activeView === 'encrypt' && <EncryptView setMessage={setMessage} pageData={pageData} setPageData={setPageData} />}
                {activeView === 'decrypt' && <DecryptView setMessage={setMessage} pageData={pageData} setPageData={setPageData} />}
            </main>
            <Footer />
        </div>
    );
}

// --- SUB-COMPONENTS for UI Sections ---

function Navigation({ activeView, setActiveView }) {
    const navButtons = ['generate', 'verify', 'encrypt', 'decrypt'];
    const labels = { generate: 'Generate Key', verify: 'Verify', encrypt: 'Encrypt', decrypt: 'Decrypt' };
    return (
        <nav className="navigation">
            {navButtons.map(view => (
                <button
                    key={view}
                    onClick={() => setActiveView(view)}
                    className={activeView === view ? 'active' : ''}
                >
                    {labels[view]}
                </button>
            ))}
        </nav>
    );
}

function TumblerAnimation() {
    const [digits, setDigits] = useState(Array(24).fill('0'));

    useEffect(() => {
        const interval = setInterval(() => {
            setDigits(d => d.map(() => (Math.random() > 0.5 ? '1' : '0')));
        }, 75);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="tumbler-container">
            {digits.map((digit, i) => (
                <div key={i} className="tumbler-digit">{digit}</div>
            ))}
        </div>
    );
}

function GenerateView({ isLoading, handleGenerateKey, result }) {
    const handleDownloadReceipt = () => {
        const receiptContent = `
QuantumTrust Key Generation Receipt
-----------------------------------
ID on Blockchain: ${result.id}
Timestamp: ${new Date(Number(result.timestamp) * 1000).toLocaleString()}
Transaction Hash: ${result.transactionHash}
-----------------------------------
SECRET VALUE (DO NOT SHARE):
Bitstring: ${result.bitstring}
-----------------------------------
PUBLIC PROOF (STORED ON CHAIN):
Commitment Hash: ${result.commitmentHash}
        `;
        const blob = new Blob([receiptContent.trim()], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url; a.download = `ID_${result.id}_receipt.txt`;
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    return (
        <div className="card">
            <h2 className="generate-title">1. Generate New Secure Key</h2>
            <p>Generate a new quantum random number. Its hash will be committed to the blockchain, and the secret will be provided in a downloadable receipt. Please save it securely.</p>
            <button className="button" onClick={handleGenerateKey} disabled={isLoading}>
                {isLoading ? 'Generating...' : 'Generate & Store'}
                {isLoading && <span className="spinner"></span>}
            </button>
            
            {isLoading && <TumblerAnimation />}

            {result && (
                <div className="result-box">
                    <h3 className="generation-complete-title">Generation Complete!</h3>
                    <p className="warning-text"><strong>IMPORTANT:</strong> The full secret bitstring is only available in the downloadable receipt. Save it now, as it cannot be recovered.</p>
                    
                    <p><strong>ID on Blockchain:</strong> <code>{result.id}</code></p>
                    <p><strong>Timestamp:</strong> <code>{new Date(Number(result.timestamp) * 1000).toLocaleString()}</code></p>
                    <p><strong>Commitment Hash:</strong> <code>{result.commitmentHash}</code></p>
                    <p><strong>Transaction Hash:</strong> <a href={`https://sepolia.etherscan.io/tx/${result.transactionHash}`} target="_blank" rel="noopener noreferrer" className="link-accent">{result.transactionHash}</a></p>

                    <div className="download-buttons">
                        <button className="button" onClick={handleDownloadReceipt}>📄 Download Full Receipt (.txt)</button>
                    </div>
                </div>
            )}
        </div>
    );
}

function VerifyView({ setMessage, pageData, setPageData }) {
    const [isLoading, setIsLoading] = useState(false);
    const { bitstring, result } = pageData.verify;
    const setBitstring = (text) => setPageData(prev => ({ ...prev, verify: { ...prev.verify, bitstring: text } }));

    const handleVerify = async () => {
        if (!bitstring) { setMessage({ text: 'Please paste a bitstring to verify.', type: 'error' }); return; }
        
        setIsLoading(true);
        setPageData(prev => ({ ...prev, verify: { ...prev.verify, result: null } }));
        setMessage({ text: '', type: '' });

        try {
            const response = await axios.post(`${API_URL}/api/verify`, { bitstring });
            setPageData(prev => ({ ...prev, verify: { ...prev.verify, result: response.data } }));
            setMessage({ text: 'Verification successful!', type: 'success' });
        } catch (error) {
            const errorData = error.response?.data || { verified: false };
            setPageData(prev => ({ ...prev, verify: { ...prev.verify, result: errorData } }));
            setMessage({ text: errorData.error || 'Verification failed.', type: 'error' });
        } finally { setIsLoading(false); }
    };

    return (
        <div className="card">
            <h2 className="verify-title">2. Verify Stored Number</h2>
            <p>Paste the secret bitstring from a saved receipt to verify its commitment on the blockchain.</p>
            <textarea className="input" value={bitstring} onChange={(e) => setBitstring(e.target.value)} placeholder="Paste the full secret bitstring here..." rows="4"></textarea>
            <button className="button" onClick={handleVerify} disabled={isLoading || !bitstring}>
                {isLoading ? 'Verifying...' : `Verify on "Blockchain"`}
                {isLoading && <span className="spinner"></span>}
            </button>
            {result && (
                <div className="result-box">
                    <h3>Verification Result</h3>
{result.verified ? (
    <>
        <p><strong>Status:</strong> <span className="pass-text">VERIFIED</span></p>
        <p><strong>ID on Blockchain:</strong> <code>{result.id}</code></p>
        <p><strong>Timestamp:</strong> <code>{new Date(Number(result.timestamp) * 1000).toLocaleString()}</code></p>
        <p><strong>Submitter Address:</strong> <code>{result.submitter}</code></p>
    </>
) : (
                        <p><strong>Status:</strong> <span className="fail-text">FAILED OR NOT FOUND</span></p>
                    )}
                </div>
            )}
        </div>
    );
}


// --- WEB CRYPTO API IMPLEMENTATION ---

const arrayBufferToBase64 = (buffer) => window.btoa(String.fromCharCode(...new Uint8Array(buffer)));
const base64ToArrayBuffer = (base64) => Uint8Array.from(window.atob(base64), c => c.charCodeAt(0));

const deriveKey = async (secretBitstring) => {
    const data = new TextEncoder().encode("encrypt:" + secretBitstring);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    return crypto.subtle.importKey('raw', hashBuffer, { name: 'AES-GCM' }, false, ['encrypt', 'decrypt']);
};

function EncryptView({ setMessage, pageData, setPageData }) {
    const { bitstring, plaintext, ciphertext } = pageData.encrypt;
    const setBitstring = (text) => setPageData(prev => ({ ...prev, encrypt: { ...prev.encrypt, bitstring: text } }));
    const setPlaintext = (text) => setPageData(prev => ({ ...prev, encrypt: { ...prev.encrypt, plaintext: text } }));
    const setCiphertext = (text) => setPageData(prev => ({ ...prev, encrypt: { ...prev.encrypt, ciphertext: text } }));

    const handleEncrypt = async () => {
        if (!bitstring || !plaintext) return;
        setMessage({text: '', type: ''});
        try {
            const cryptoKey = await deriveKey(bitstring);
            const iv = crypto.getRandomValues(new Uint8Array(12));
            const encryptedBuffer = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, cryptoKey, new TextEncoder().encode(plaintext));
            setCiphertext(`${arrayBufferToBase64(iv)}:${arrayBufferToBase64(encryptedBuffer)}`);
            setMessage({ text: 'Encryption successful!', type: 'success' });
        } catch (error) {
            setMessage({ text: `Encryption failed: ${error.message}`, type: 'error' });
        }
    };
    
    return (
        <div className="card">
            <h2 className="encrypt-title">Encrypt Message (AES-256-GCM)</h2>
            <p>Paste the secret bitstring to use as a key, then enter your message and click Encrypt.</p>
            <textarea className="input" value={bitstring} onChange={(e) => setBitstring(e.target.value)} placeholder="Paste secret bitstring here..." rows={3}></textarea>
            <textarea className="input" value={plaintext} onChange={(e) => setPlaintext(e.target.value)} placeholder="Enter your secret message here..."></textarea>
            <button className="button" onClick={handleEncrypt} disabled={!bitstring || !plaintext}>Encrypt Message</button>
            {ciphertext && (
                <div className="result-box">
                    <div className="result-box-header">
                        <h3 className="encrypted-title">Encrypted Message (Ciphertext)</h3>
                        <button className="copy-button" onClick={() => navigator.clipboard.writeText(ciphertext)}>Copy</button>
                    </div>
                    <textarea className="input" value={ciphertext} readOnly></textarea>
                </div>
            )}
        </div>
    );
}

function DecryptView({ setMessage, pageData, setPageData }) {
    const { bitstring, ciphertext, decryptedText } = pageData.decrypt;
    const setBitstring = (text) => setPageData(prev => ({ ...prev, decrypt: { ...prev.decrypt, bitstring: text } }));
    const setCiphertext = (text) => setPageData(prev => ({ ...prev, decrypt: { ...prev.decrypt, ciphertext: text } }));
    const setDecryptedText = (text) => setPageData(prev => ({ ...prev, decrypt: { ...prev.decrypt, decryptedText: text } }));

    const handleDecrypt = async () => {
        if (!bitstring || !ciphertext) return;
        setMessage({ text: '', type: '' });
        try {
            const cryptoKey = await deriveKey(bitstring);
            const parts = ciphertext.split(':');
            if (parts.length !== 2) throw new Error("Invalid format.");
            
            const decryptedBuffer = await crypto.subtle.decrypt({ name: 'AES-GCM', iv: base64ToArrayBuffer(parts[0]) }, cryptoKey, base64ToArrayBuffer(parts[1]));
            const plaintext = new TextDecoder().decode(decryptedBuffer);
            
            setDecryptedText(plaintext);
            setMessage({ text: 'Decryption successful!', type: 'success' });
        } catch (error) {
            setMessage({ text: 'Decryption failed. Key may be incorrect or data was tampered with.', type: 'error' });
        }
    };

    return (
        <div className="card">
            <h2 className="decrypt-title">Decrypt Message (AES-256-GCM)</h2>
            <p>Paste the secret bitstring and the full ciphertext, then click Decrypt.</p>
            <textarea className="input" value={bitstring} onChange={(e) => setBitstring(e.target.value)} placeholder="Paste secret bitstring here..." rows={3}></textarea>
            <textarea className="input" value={ciphertext} onChange={(e) => setCiphertext(e.target.value)} placeholder="Paste the full ciphertext from the encryption step..."></textarea>
            <button className="button" onClick={handleDecrypt} disabled={!bitstring || !ciphertext}>Decrypt Message</button>
            {decryptedText && (
                <div className="result-box">
                    <div className="result-box-header">
                         <h3 className="decrypted-title">Decrypted Message (Plaintext)</h3>
                    </div>
                    <p>{decryptedText}</p>
                </div>
            )}
        </div>
    );
}

export default App;


import React from 'react';

/**
 * The main header component, redesigned to match the professional screenshots.
 * It displays the project title, subtitle, and the connected wallet account.
 */
function Header({ account }) {
    return (
        <header className="header">
            <div className="header-content">
                <h1>QuantumTrust</h1>
                <p>A Verifiable Source of Quantum Randomness on the Blockchain</p>
            </div>
            {account && (
                <div className="account-display">
                    Connected Account: <code>{`${account.substring(0, 6)}...${account.substring(account.length - 4)}`}</code>
                </div>
            )}
        </header>
    );
}

export default Header;



# QuantumTrust: A Verifiable Quantum Randomness Oracle

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python) ![React](https://img.shields.io/badge/React-18-blue?logo=react) ![Solidity](https://img.shields.io/badge/Solidity-0.8.19-lightgrey?logo=solidity)

This repository contains the full working prototype for **QuantumTrust**, a decentralized service for providing true, statistically validated, and publicly verifiable quantum randomness.

This project was developed for the **Amaravati Quantum Valley Hackathon 2025** (Problem Statement AQVH910). It provides a complete end-to-end solution, moving from the fundamental principles of quantum mechanics to a secure, user-friendly application with on-chain proof.

## Table of Contents
- [Core Features](#core-features)
- [How It Works](#how-it-works)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Setup and Installation](#setup-and-installation)
- [Running the Application](#running-the-application)
- [Future Vision](#future-vision)

## Core Features

- **Quantum Randomness Generation**: Utilizes a **Qiskit**-simulated quantum circuit with Hadamard gates and measurement to produce high-entropy, physically unpredictable random bitstrings.
- **Commit-Reveal Verification On-Chain**: Implements a secure commit-reveal protocol. Instead of storing the secret, a **SHA-256 hash** of the number is immutably stored on the **Sepolia testnet**, creating a tamper-proof audit trail.
- **Full-Stack dApp**: A complete system featuring a **React** frontend, a **Python/Flask** backend, and a **Solidity** smart contract.
- **Client-Side Encryption (AES-GCM)**: Demonstrates a real-world use case by allowing users to perform secure, authenticated encryption and decryption in the browser using the **Web Crypto API** with the quantum-generated key.
- **Statistical Analysis Dashboard**: Includes a standalone dashboard that runs a suite of **NIST-based statistical tests** on a large (~50,000 bit) sample, providing live, visual proof of the randomness quality.

## How It Works

The system follows a four-stage workflow to ensure both security and verifiability.

*_Placeholder for a clean, dark-themed workflow diagram showing the 4 steps below_*

1. **Generate**: A 264-bit quantum number is created using a **Qiskit**-simulated circuit in the **Python** backend.
2. **Commit**: A **SHA-256 hash** of the number is sent as a transaction and stored on the **Sepolia blockchain** via our **Solidity** smart contract.
3. **Verify**: The **React dApp** allows a user to provide their secret bitstring, which is re-hashed and verified against the immutable on-chain commitment.
4. **Apply**: The verified random number is used to derive a key for secure **AES-256-GCM** encryption, performed entirely on the client side.

## Technology Stack

- **Quantum Engine**: **Python** 3.11, **Qiskit**, **Qiskit Aer**
- **Backend API**: **Flask**, **Web3.py**
- **Blockchain**: **Solidity** ^0.8.19, **Ethereum (Sepolia Testnet)**
- **Frontend**: **React** 18, **Axios**, **Web Crypto API**
- **Analysis Dashboard**: **HTML**, **Vanilla JavaScript**, **Chart.js**
- **Infrastructure**: **Alchemy** (for Sepolia node access)

## Project Structure

```plaintext
QuantumTrust/
├── backend/
│   ├── app.py
│   ├── blockchain/
│   │   ├── contract.sol
│   │   └── deploy.py
│   └── qrng/
│       ├── generator.py
│       └── analyzer.py
├── frontend/
│   ├── public/
│   │   └── analysis.html
│   └── src/
│       ├── App.js
│       └── styles.css
```

## Setup and Installation

Follow these steps to set up and run the project locally.

### Prerequisites

- **Python** 3.10 or later
- **Node.js** (LTS version)
- A browser with the **MetaMask** extension installed and configured for the **Sepolia testnet**

### Project Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/shanthrajkandru-arch/Quantum-Trust.git
   ```

2. Open a terminal (PowerShell on Windows, or default terminal on Mac/Linux).

3. Set up the **Python** backend:
   ```bash
   cd backend
   python -m venv venv
   # Activate the virtual environment
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # On Mac/Linux:
   source venv/bin/activate
   pip install -r requirements.txt
   cd ..
   ```

4. Set up the **Frontend**:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

### Configuration

The backend server requires your personal blockchain credentials.

1. In the `backend` directory, copy the example `.env` file:
   ```bash
   # On Windows:
   copy .env.example .env
   # On Mac/Linux:
   cp .env.example .env
   ```

2. Edit the new `.env` file and fill in your values:
   - `WEB3_PROVIDER_URI`: Your personal HTTPS API key URL from **Alchemy** for the **Sepolia testnet**
   - `PRIVATE_KEY`: The private key of your **MetaMask** account (funded with Sepolia ETH). Must start with `0x`
   - `DEPLOYER_ADDRESS`: The public address of the same account
   - `CHAIN_ID`: `11155111` for **Sepolia**

## Running the Application

This project requires two separate terminals.

### Terminal 1: Run the Backend

1. Open a terminal in the root project directory.
2. Activate the **Python** virtual environment as shown in the setup steps.
3. (Run Once) Deploy the **Smart Contract**:
   ```bash
   python backend/blockchain/deploy.py
   ```
4. Start the **Backend Server** and leave this terminal running:
   ```bash
   python backend/app.py
   ```

### Terminal 2: Run the Frontend

1. Open a new terminal in the root project directory.
2. Start the **React Application** and leave this terminal running:
   ```bash
   cd frontend
   npm start
   ```

Your browser will automatically open to `http://localhost:3000`, where you can interact with the live application.

## Future Vision

This successful prototype is the foundation for a fully decentralized, production-ready protocol. Our roadmap is focused on three key areas to transform **QuantumTrust** into a foundational piece of Web3 infrastructure:

- **Transition to Real Quantum Hardware**: Replace the **Qiskit** simulator with a connection to real quantum processors (e.g., via **IBM Quantum**) and integrate high-speed physical **QRNGs**. This will provide true, physically sourced non-determinism and higher throughput.
- **Deploy on Layer-2s & Decentralize**: Deploy the smart contract on **Layer-2 rollups** like **Optimism** or **Arbitrum**. Evolve the backend from a single server into a decentralized oracle network to eliminate any single point of failure.
- **Implement Future-Proof Security**: Incorporate **Post-Quantum Cryptography (PQC)** for all classical cryptographic functions and implement **Zero-Knowledge Proofs (ZKPs)** to enable private verification of randomness.
```


import os
import json
import hashlib
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from web3 import Web3
from threading import Lock

# --- Local Imports ---
from qrng.generator import QuantumRNG
from qrng.analyzer import perform_full_analysis

# --- Load Environment Variables ---
load_dotenv()  # Loads .env file so you can access DEPLOYER_ADDRESS, PRIVATE_KEY, etc.

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing (frontend can call API)

# --- Global Variables & Thread Lock ---
w3 = None  # Web3 connection object
contract = None  # Smart contract instance
deployer_address = os.getenv("DEPLOYER_ADDRESS")  # Ethereum address deploying/using contract
private_key = os.getenv("PRIVATE_KEY")  # Corresponding private key
qrng = QuantumRNG()  # Initialize the quantum RNG
nonce_lock = Lock()  # Lock to prevent transaction nonce conflicts

# --- Helper Function to Load Contract ---
def load_contract():
    """
    Loads the smart contract using ABI and address from local JSON,
    then connects to the blockchain provider.
    """
    global w3, contract
    try:
        # Load contract info
        contract_info_path = os.path.join(os.path.dirname(__file__), 'contract-info.json')
        with open(contract_info_path) as f:
            info = json.load(f)
        contract_abi = info["abi"]
        contract_address = info["address"]

        # Connect to blockchain provider
        provider_uri = os.getenv("WEB3_PROVIDER_URI")
        w3 = Web3(Web3.HTTPProvider(provider_uri))
        
        if not w3.is_connected():
            print("❌ Failed to connect to the blockchain.")
            return False

        # Instantiate contract object
        contract = w3.eth.contract(address=contract_address, abi=contract_abi)
        print(f"✅ Successfully connected to blockchain and loaded contract at {contract_address}")
        return True

    except Exception as e:
        print(f"❌ Error loading contract: {e}")
        return False

# --- API Endpoints ---

@app.route('/api/generate', methods=['POST'])
def generate_and_store():
    """
    Generates a quantum 264-bit random string, creates a public commitment hash,
    stores it on-chain, and returns all related metadata to the user.
    """
    if not contract or not w3:
        return jsonify({"error": "Backend not configured."}), 500

    try:
        # 1. Generate a secure, 264-bit random string using QRNG
        bitstring = qrng.generate_random_bitstring(264)
        
        # 2. Prefix for domain separation & hash with SHA256
        prefixed_string = "verify:" + bitstring
        commitment_hash_bytes = hashlib.sha256(prefixed_string.encode('utf-8')).digest()

        # 3. Prepare and send the transaction securely
        with nonce_lock:  # Acquire lock to avoid nonce race conditions
            nonce = w3.eth.get_transaction_count(deployer_address)
            
            store_transaction = contract.functions.storeCommitment(commitment_hash_bytes).build_transaction({
                'chainId': int(os.getenv("CHAIN_ID")),
                'from': deployer_address,
                'nonce': nonce,
                'gas': 200000,
                'gasPrice': w3.eth.gas_price
            })

            # Sign and broadcast the transaction
            signed_txn = w3.eth.account.sign_transaction(store_transaction, private_key=private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Wait for transaction to be mined
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # 4. Extract relevant event logs (CommitmentStored)
        logs = contract.events.CommitmentStored().process_receipt(tx_receipt)
        new_id = logs[0]['args']['id']
        block = w3.eth.get_block(tx_receipt.blockNumber)

        print(f"Successfully stored commitment for ID: {new_id}")
        
        # 5. Return metadata to user
        return jsonify({
            "id": new_id,
            "bitstring": bitstring,
            "commitmentHash": "0x" + commitment_hash_bytes.hex(),
            "transactionHash": tx_hash.hex(),
            "timestamp": block.timestamp
        }), 201

    except Exception as e:
        print(f"Error during generation: {e}")
        return jsonify({"error": "An error occurred during key generation."}), 500


@app.route('/api/verify', methods=['POST'])
def verify_commitment():
    """
    Verifies whether a given bitstring matches a previously stored commitment on-chain.
    """
    if not contract or not w3:
        return jsonify({"error": "Backend not configured."}), 500

    try:
        data = request.get_json()
        bitstring = data.get('bitstring')

        if not bitstring:
            return jsonify({"error": "Bitstring is required for verification."}), 400

        # 1. Recreate the commitment hash exactly as done during storage
        prefixed_string = "verify:" + bitstring
        commitment_hash_to_check = hashlib.sha256(prefixed_string.encode('utf-8')).digest()
        
        # 2. Call the smart contract to check for the hash's existence
        id, submitter, timestamp = contract.functions.getCommitment(commitment_hash_to_check).call()
        
        # 3. Return verification result
        return jsonify({
            "verified": True,
            "id": id,
            "submitter": submitter,
            "timestamp": timestamp,
            "commitmentHash": "0x" + commitment_hash_to_check.hex()  # Always return commitment hash
        }), 200

    except Exception as e:
        print(f"Error during verification: {e}")
        return jsonify({
            "error": "Verification failed. The number may not exist or is incorrect.",
            "verified": False
        }), 404


@app.route('/api/analyze-randomness', methods=['POST'])
def run_analysis():
    """
    Runs full quantum randomness analysis (NIST tests) on a sample bitstring.
    Returns all results to frontend for visualization.
    """
    try:
        analysis_results = perform_full_analysis(sample_bits=128)
        return jsonify(analysis_results), 200
    except Exception as e:
        print(f"Error during analysis: {e}")
        return jsonify({"error": "An error occurred during analysis."}), 500

# --- Main Execution ---
if __name__ == '__main__':
    # Only run server if contract loads successfully
    if load_contract():
        app.run(host='0.0.0.0', port=5000)

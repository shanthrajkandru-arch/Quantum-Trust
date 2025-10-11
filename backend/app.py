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
load_dotenv()

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app) 

# --- Global Variables & Thread Lock ---
w3 = None
contract = None
deployer_address = os.getenv("DEPLOYER_ADDRESS")
private_key = os.getenv("PRIVATE_KEY")
qrng = QuantumRNG()
nonce_lock = Lock() # To prevent transaction race conditions

# --- Helper Function to Load Contract ---
def load_contract():
    global w3, contract
    try:
        contract_info_path = os.path.join(os.path.dirname(__file__), 'contract-info.json')
        with open(contract_info_path) as f:
            info = json.load(f)
        contract_abi = info["abi"]
        contract_address = info["address"]

        provider_uri = os.getenv("WEB3_PROVIDER_URI")
        w3 = Web3(Web3.HTTPProvider(provider_uri))
        
        if not w3.is_connected():
            print("❌ Failed to connect to the blockchain.")
            return False

        contract = w3.eth.contract(address=contract_address, abi=contract_abi)
        print(f"✅ Successfully connected to blockchain and loaded contract at {contract_address}")
        return True

    except Exception as e:
        print(f"❌ Error loading contract: {e}")
        return False

# --- API Endpoints ---

@app.route('/api/generate', methods=['POST'])
def generate_and_store():
    if not contract or not w3:
        return jsonify({"error": "Backend not configured."}), 500

    try:
        # 1. Generate a secure, 264-bit random string
        bitstring = qrng.generate_random_bitstring(264)
        
        # 2. Create the public commitment hash (with domain separation)
        prefixed_string = "verify:" + bitstring
        commitment_hash_bytes = hashlib.sha256(prefixed_string.encode('utf-8')).digest()

        # 3. Prepare and send the transaction securely
        with nonce_lock: # Acquire lock to prevent race conditions
            nonce = w3.eth.get_transaction_count(deployer_address)
            
            store_transaction = contract.functions.storeCommitment(commitment_hash_bytes).build_transaction({
                'chainId': int(os.getenv("CHAIN_ID")),
                'from': deployer_address,
                'nonce': nonce,
                'gas': 200000,
                'gasPrice': w3.eth.gas_price
            })

            signed_txn = w3.eth.account.sign_transaction(store_transaction, private_key=private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # 4. Get data from event logs
        logs = contract.events.CommitmentStored().process_receipt(tx_receipt)
        new_id = logs[0]['args']['id']
        block = w3.eth.get_block(tx_receipt.blockNumber)

        print(f"Successfully stored commitment for ID: {new_id}")
        
        # 5. Return all necessary data to the user
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
    if not contract or not w3:
        return jsonify({"error": "Backend not configured."}), 500

    try:
        data = request.get_json()
        bitstring = data.get('bitstring')

        if not bitstring:
            return jsonify({"error": "Bitstring is required for verification."}), 400

        # 1. Recreate the exact same commitment hash
        prefixed_string = "verify:" + bitstring
        commitment_hash_to_check = hashlib.sha256(prefixed_string.encode('utf-8')).digest()
        
        # 2. Call the contract to check for the hash's existence
        id, submitter, timestamp = contract.functions.getCommitment(commitment_hash_to_check).call()
        
        # --- FIX: Ensure the commitment hash is always returned ---
        return jsonify({
            "verified": True,
            "id": id,
            "submitter": submitter,
            "timestamp": timestamp,
            "commitmentHash": "0x" + commitment_hash_to_check.hex() # Added this line
        }), 200

    except Exception as e:
        print(f"Error during verification: {e}")
        return jsonify({"error": "Verification failed. The number may not exist or is incorrect.", "verified": False}), 404


@app.route('/api/analyze-randomness', methods=['POST'])
def run_analysis():
    # This endpoint remains the same, it is self-contained
    try:
        analysis_results = perform_full_analysis(sample_bits=128)
        return jsonify(analysis_results), 200
    except Exception as e:
        print(f"Error during analysis: {e}")
        return jsonify({"error": "An error occurred during analysis."}), 500

# --- Main Execution ---
if __name__ == '__main__':
    if load_contract():
        app.run(host='0.0.0.0', port=5000)


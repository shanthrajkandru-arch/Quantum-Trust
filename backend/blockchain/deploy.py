import os
import json
from web3 import Web3
from dotenv import load_dotenv
from solcx import compile_standard, install_solc

# --- Load Environment Variables ---
# NEW, MORE ROBUST PATH FINDING:
# This builds an absolute path to the .env file, making it more reliable.
script_dir = os.path.dirname(__file__)
dotenv_path = os.path.join(script_dir, '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- Solidity Compiler Setup ---
def compile_contract():
    """Compiles the Solidity smart contract."""
    try:
        # Automatically install the required Solidity compiler version
        solc_version = "0.8.19"
        print(f"Installing solc version {solc_version}...")
        install_solc(solc_version)
        print("Compiler installed.")

        # --- CORRECTED FILE PATH ---
        # Build an absolute path to the contract.sol file
        contract_path = os.path.join(os.path.dirname(__file__), "contract.sol")
        with open(contract_path, "r") as f:
            contract_source_code = f.read()

        compiled_sol = compile_standard(
            {
                "language": "Solidity",
                "sources": {"contract.sol": {"content": contract_source_code}},
                "settings": {
                    "outputSelection": {
                        "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
                    }
                },
            },
            solc_version=solc_version,
        )
        
        # Get the contract name (assuming it's the same as the file name without extension)
        contract_name = "QuantumTrust"
        bytecode = compiled_sol["contracts"]["contract.sol"][contract_name]["evm"]["bytecode"]["object"]
        abi = json.loads(compiled_sol["contracts"]["contract.sol"][contract_name]["metadata"])["output"]["abi"]
        
        return bytecode, abi
    except Exception as e:
        print(f"❌ Error during contract compilation: {e}")
        raise

# --- Main Deployment Logic ---
def main():
    """Connects to the blockchain, deploys the contract, and saves the info."""
    print("🚀 Starting deployment process...")
    
    # Connect to the blockchain
    provider_uri = os.getenv("WEB3_PROVIDER_URI")
    
    # --- NEW DEBUGGING CHECK ---
    print(f"Attempting to connect with URI: {provider_uri}")
    if not provider_uri:
        print("❌ WEB3_PROVIDER_URI not found. Please check your .env file and its path.")
        return

    w3 = Web3(Web3.HTTPProvider(provider_uri))
    if not w3.is_connected():
        print("❌ Failed to connect to the blockchain. Please verify your Alchemy/Infura URL and API key.")
        return

    deployer_address = os.getenv("DEPLOYER_ADDRESS")
    private_key = os.getenv("PRIVATE_KEY")
    chain_id = int(os.getenv("CHAIN_ID"))
    
    print("Compiling contract...")
    bytecode, abi = compile_contract()
    
    # Create the contract instance
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    print("Building deployment transaction...")
    nonce = w3.eth.get_transaction_count(deployer_address)
    tx = Contract.constructor().build_transaction({
        "chainId": chain_id,
        "from": deployer_address,
        "nonce": nonce,
        "gasPrice": w3.eth.gas_price
    })
    
    print("Signing transaction...")
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    
    print("Sending transaction...")
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"Transaction sent! Hash: {tx_hash.hex()}")
    
    print("Waiting for transaction receipt...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    contract_address = tx_receipt.contractAddress
    print(f"✅ Contract deployed successfully at address: {contract_address}")
    
    # Save contract info to a file for the backend and frontend to use
    contract_info = {
        "address": contract_address,
        "abi": abi
    }
    # Save it in the 'backend' directory
    info_path = os.path.join(os.path.dirname(__file__), '..', 'contract-info.json')
    with open(info_path, "w") as f:
        json.dump(contract_info, f, indent=2)
    print(f"📝 Contract info saved to {info_path}")

if __name__ == "__main__":
    main()


import os
import json
from web3 import Web3
from dotenv import load_dotenv
from solcx import compile_standard, install_solc

# --- Load Environment Variables ---
# Instead of relying on the current working directory, build a robust absolute path to the .env file
script_dir = os.path.dirname(__file__)  # Directory of this script
dotenv_path = os.path.join(script_dir, '..', '..', '.env')  # Relative path to project root .env
load_dotenv(dotenv_path=dotenv_path)  # Load variables like WEB3_PROVIDER_URI, DEPLOYER_ADDRESS, PRIVATE_KEY, CHAIN_ID

# --- Solidity Compiler Setup ---
def compile_contract():
    """
    Compiles the Solidity smart contract using solcx.
    Returns the contract's bytecode and ABI.
    """
    try:
        # Ensure correct compiler version is installed
        solc_version = "0.8.19"
        print(f"Installing solc version {solc_version}...")
        install_solc(solc_version)
        print("Compiler installed.")

        # Build an absolute path to the contract.sol file
        contract_path = os.path.join(os.path.dirname(__file__), "contract.sol")
        with open(contract_path, "r") as f:
            contract_source_code = f.read()  # Read contract source code

        # Compile contract using solcx
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
        
        # Assume contract name matches the main contract class inside the file
        contract_name = "QuantumTrust"
        bytecode = compiled_sol["contracts"]["contract.sol"][contract_name]["evm"]["bytecode"]["object"]
        abi = json.loads(compiled_sol["contracts"]["contract.sol"][contract_name]["metadata"])["output"]["abi"]
        
        return bytecode, abi
    except Exception as e:
        print(f"❌ Error during contract compilation: {e}")
        raise

# --- Main Deployment Logic ---
def main():
    """
    Connects to blockchain, deploys the contract, waits for confirmation,
    and saves ABI + deployed address to JSON.
    """
    print("🚀 Starting deployment process...")
    
    # Connect to blockchain provider (e.g., Infura, Alchemy)
    provider_uri = os.getenv("WEB3_PROVIDER_URI")
    
    # Debugging / safety check
    print(f"Attempting to connect with URI: {provider_uri}")
    if not provider_uri:
        print("❌ WEB3_PROVIDER_URI not found. Please check your .env file and its path.")
        return

    w3 = Web3(Web3.HTTPProvider(provider_uri))
    if not w3.is_connected():
        print("❌ Failed to connect to the blockchain. Check your provider URL or network.")
        return

    # Load deployer credentials from environment
    deployer_address = os.getenv("DEPLOYER_ADDRESS")
    private_key = os.getenv("PRIVATE_KEY")
    chain_id = int(os.getenv("CHAIN_ID"))
    
    # Compile the Solidity contract
    print("Compiling contract...")
    bytecode, abi = compile_contract()
    
    # Create a contract instance to deploy
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    # Prepare deployment transaction
    print("Building deployment transaction...")
    nonce = w3.eth.get_transaction_count(deployer_address)  # Avoid nonce conflicts
    tx = Contract.constructor().build_transaction({
        "chainId": chain_id,
        "from": deployer_address,
        "nonce": nonce,
        "gasPrice": w3.eth.gas_price
    })
    
    # Sign the deployment transaction using deployer's private key
    print("Signing transaction...")
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    
    # Send the transaction to the network
    print("Sending transaction...")
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"Transaction sent! Hash: {tx_hash.hex()}")
    
    # Wait for the transaction to be mined and confirmed
    print("Waiting for transaction receipt...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    # Extract deployed contract address
    contract_address = tx_receipt.contractAddress
    print(f"✅ Contract deployed successfully at address: {contract_address}")
    
    # Save contract info (ABI + address) for backend/frontend use
    contract_info = {
        "address": contract_address,
        "abi": abi
    }
    info_path = os.path.join(os.path.dirname(__file__), '..', 'contract-info.json')
    with open(info_path, "w") as f:
        json.dump(contract_info, f, indent=2)
    print(f"📝 Contract info saved to {info_path}")

# --- Entry Point ---
if __name__ == "__main__":
    main()

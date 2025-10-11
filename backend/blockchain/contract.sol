// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title QuantumTrust v2
 * @dev This contract implements a secure commit-reveal scheme. It stores a
 * SHA-256 hash (a "commitment") of a quantum random number, not the number
 * itself. This acts as a public, immutable notary service to prove a
 * number's existence and timestamp without ever revealing the secret number.
 */
contract QuantumTrust {

    // --- Data Structures ---

    struct Commitment {
        uint256 id;          // The unique, user-friendly ID for this commitment
        address submitter;   // The address that submitted the hash
        uint256 timestamp;   // The block timestamp of when the hash was stored
    }

    // --- State Variables ---

    // Primary mapping for verification: hash -> Commitment details.
    // This allows for a fast, direct lookup to check if a hash exists.
    mapping(bytes32 => Commitment) private _commitments;

    // Secondary mapping for user convenience: ID -> hash.
    // This allows retrieving a public hash using its simple ID.
    mapping(uint256 => bytes32) private _idToCommitmentHash;
    
    // Counter for generating new unique IDs.
    uint256 private _commitmentCounter;

    // --- Events ---

    event CommitmentStored(
        uint256 indexed id,
        bytes32 indexed commitmentHash,
        address indexed submitter
    );

    // --- Core Functions ---

    /**
     * @dev Stores a hash commitment on the blockchain.
     * @param _commitmentHash The SHA-256 hash of the secret bitstring.
     * @return The new unique ID assigned to this commitment.
     */
    function storeCommitment(bytes32 _commitmentHash) public returns (uint256) {
        // Require that the hash has not been submitted before to prevent replays.
        require(_commitments[_commitmentHash].submitter == address(0), "Commitment hash already exists");

        _commitmentCounter++;
        uint256 newId = _commitmentCounter;

        // Store the commitment details in the primary mapping.
        _commitments[_commitmentHash] = Commitment({
            id: newId,
            submitter: msg.sender,
            timestamp: block.timestamp
        });

        // Link the new ID to the hash in the secondary mapping.
        _idToCommitmentHash[newId] = _commitmentHash;

        emit CommitmentStored(newId, _commitmentHash, msg.sender);
        return newId;
    }

    // --- Getter & Verification Functions ---

    /**
     * @dev Checks for the existence of a commitment and returns its details.
     * This is the primary verification function.
     * @param _commitmentHash The hash to verify.
     * @return The ID, submitter address, and timestamp of the commitment.
     */
    function getCommitment(bytes32 _commitmentHash) public view returns (uint256, address, uint256) {
        Commitment storage commitment = _commitments[_commitmentHash];
        // If the submitter is the zero address, the commitment does not exist.
        require(commitment.submitter != address(0), "Commitment not found");
        return (commitment.id, commitment.submitter, commitment.timestamp);
    }
    
    /**
     * @dev Retrieves a commitment hash using its user-friendly ID.
     * @param _id The ID to look up.
     * @return The bytes32 hash associated with the ID.
     */
    function getCommitmentHashById(uint256 _id) public view returns (bytes32) {
        bytes32 commitmentHash = _idToCommitmentHash[_id];
        require(commitmentHash != 0, "Invalid ID");
        return commitmentHash;
    }

    /**
     * @dev Returns the total number of commitments stored in the contract.
     */
    function getCommitmentCount() public view returns (uint256) {
        return _commitmentCounter;
    }
}

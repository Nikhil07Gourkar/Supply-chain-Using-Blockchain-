// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title SecureSupplyChain
 * @author Final Year Engineering Project
 * @notice Phase 3 — Blockchain Core: Stores verified ML fingerprints on-chain
 *
 * Deployment targets:
 *   - Local Dev  : Ganache (http://127.0.0.1:7545)
 *   - Testnet    : Ethereum Sepolia (ChainID: 11155111)
 *
 * PBFT Note:
 *   On a private/consortium chain (e.g., Hyperledger Besu with PBFT),
 *   the consensus is handled at the network layer.
 *   This Solidity contract is the application layer — it records
 *   only PBFT-committed (verified) data.
 *
 * Architecture:
 *   Off-chain ML (Python) → SHA-256 Hash → FastAPI Bridge → Web3.js
 *   → submitRecord() → Event emitted → React Dashboard reads events
 */
contract SecureSupplyChain {

    // ─────────────────────────────────────────────
    // DATA STRUCTURES
    // ─────────────────────────────────────────────

    /**
     * @dev SupplyChainRecord: One immutable record per transaction
     * @param dataHash       SHA-256 fingerprint of ML output (bytes32)
     * @param participantId  Supply chain actor (supplier, logistics, retailer)
     * @param recordType     Type: "PREDICTION", "ANOMALY", "SHIPMENT"
     * @param riskScore      Attention-weighted risk score (0–100, scaled ×100)
     * @param isAnomaly      True if Isolation Forest flagged as fraudulent
     * @param timestamp      Block timestamp (Unix epoch)
     * @param blockNumber    Block number for auditability
     * @param isVerified     PBFT consensus verified flag
     */
    struct SupplyChainRecord {
        bytes32  dataHash;
        string   participantId;
        string   recordType;
        uint16   riskScore;       // 0–10000 (actual score × 100 for 2 decimals)
        bool     isAnomaly;
        uint256  timestamp;
        uint256  blockNumber;
        bool     isVerified;
    }

    // ─────────────────────────────────────────────
    // STATE VARIABLES
    // ─────────────────────────────────────────────

    address public owner;
    address public pbftCoordinator;  // Authorized PBFT coordinator node

    uint256 public recordCount;
    mapping(uint256 => SupplyChainRecord) private records;

    // Quick lookup: hash → record ID
    mapping(bytes32 => uint256) public hashToRecordId;

    // Participant whitelist (for private supply chain network)
    mapping(address => bool) public authorizedNodes;
    mapping(address => string) public nodeParticipantId;

    // Anomaly counter per participant
    mapping(string => uint256) public anomalyCount;

    // ─────────────────────────────────────────────
    // EVENTS (consumed by React Dashboard via Web3.js)
    // ─────────────────────────────────────────────

    event RecordSubmitted(
        uint256 indexed recordId,
        bytes32 indexed dataHash,
        string  participantId,
        string  recordType,
        uint16  riskScore,
        bool    isAnomaly,
        uint256 timestamp
    );

    event AnomalyFlagged(
        uint256 indexed recordId,
        string  participantId,
        uint256 anomalyCount,
        uint256 timestamp
    );

    event NodeAuthorized(address indexed node, string participantId);
    event NodeRevoked(address indexed node);
    event PBFTCoordinatorUpdated(address indexed newCoordinator);

    // ─────────────────────────────────────────────
    // MODIFIERS
    // ─────────────────────────────────────────────

    modifier onlyOwner() {
        require(msg.sender == owner, "SCM: Not owner");
        _;
    }

    modifier onlyAuthorized() {
        require(
            authorizedNodes[msg.sender] || msg.sender == owner,
            "SCM: Unauthorized node"
        );
        _;
    }

    modifier onlyPBFTCoordinator() {
        require(
            msg.sender == pbftCoordinator || msg.sender == owner,
            "SCM: Not PBFT coordinator"
        );
        _;
    }

    modifier validHash(bytes32 _hash) {
        require(_hash != bytes32(0), "SCM: Invalid hash");
        require(hashToRecordId[_hash] == 0, "SCM: Duplicate hash");
        _;
    }

    // ─────────────────────────────────────────────
    // CONSTRUCTOR
    // ─────────────────────────────────────────────

    /**
     * @param _pbftCoordinator Address of the PBFT leader/coordinator node
     */
    constructor(address _pbftCoordinator) {
        owner = msg.sender;
        pbftCoordinator = _pbftCoordinator;
        authorizedNodes[msg.sender] = true;
        nodeParticipantId[msg.sender] = "GENESIS_NODE";
        recordCount = 0;
    }

    // ─────────────────────────────────────────────
    // CORE FUNCTIONS
    // ─────────────────────────────────────────────

    /**
     * @notice Submit a verified supply chain record after PBFT consensus
     * @dev Called by the FastAPI bridge after PBFT commit phase completes
     *
     * PBFT Flow (off-chain, managed by coordinator):
     *   1. PRE-PREPARE : Leader broadcasts ML hash + record metadata
     *   2. PREPARE     : Replica nodes validate and broadcast PREPARE messages
     *   3. COMMIT      : After 2f+1 PREPARE msgs, COMMIT phase starts
     *   4. REPLY       : After 2f+1 COMMIT msgs, this function is called
     *
     * @param _dataHash      SHA-256 fingerprint from Python ML pipeline
     * @param _participantId Supply chain participant identifier
     * @param _recordType    "PREDICTION" | "ANOMALY" | "SHIPMENT" | "AUDIT"
     * @param _riskScore     Risk score × 100 (e.g., 75.50 → 7550)
     * @param _isAnomaly     Isolation Forest anomaly flag
     */
    function submitRecord(
        bytes32 _dataHash,
        string  calldata _participantId,
        string  calldata _recordType,
        uint16  _riskScore,
        bool    _isAnomaly
    )
        external
        onlyAuthorized
        validHash(_dataHash)
        returns (uint256 recordId)
    {
        require(bytes(_participantId).length > 0, "SCM: Empty participant ID");
        require(_riskScore <= 10000, "SCM: Risk score out of range");

        recordCount++;
        recordId = recordCount;

        records[recordId] = SupplyChainRecord({
            dataHash:      _dataHash,
            participantId: _participantId,
            recordType:    _recordType,
            riskScore:     _riskScore,
            isAnomaly:     _isAnomaly,
            timestamp:     block.timestamp,
            blockNumber:   block.number,
            isVerified:    true
        });

        hashToRecordId[_dataHash] = recordId;

        emit RecordSubmitted(
            recordId,
            _dataHash,
            _participantId,
            _recordType,
            _riskScore,
            _isAnomaly,
            block.timestamp
        );

        if (_isAnomaly) {
            anomalyCount[_participantId]++;
            emit AnomalyFlagged(
                recordId,
                _participantId,
                anomalyCount[_participantId],
                block.timestamp
            );
        }

        return recordId;
    }

    /**
     * @notice Batch submit multiple records (gas-efficient for high throughput)
     * @dev Array lengths must match; max 50 records per batch
     */
    function batchSubmitRecords(
        bytes32[] calldata _hashes,
        string[]  calldata _participantIds,
        string[]  calldata _recordTypes,
        uint16[]  calldata _riskScores,
        bool[]    calldata _isAnomalies
    ) external onlyAuthorized {
        uint256 len = _hashes.length;
        require(len > 0 && len <= 50, "SCM: Batch size 1-50");
        require(
            len == _participantIds.length &&
            len == _recordTypes.length &&
            len == _riskScores.length &&
            len == _isAnomalies.length,
            "SCM: Array length mismatch"
        );

        for (uint256 i = 0; i < len; i++) {
            if (_hashes[i] != bytes32(0) && hashToRecordId[_hashes[i]] == 0) {
                recordCount++;
                records[recordCount] = SupplyChainRecord({
                    dataHash:      _hashes[i],
                    participantId: _participantIds[i],
                    recordType:    _recordTypes[i],
                    riskScore:     _riskScores[i],
                    isAnomaly:     _isAnomalies[i],
                    timestamp:     block.timestamp,
                    blockNumber:   block.number,
                    isVerified:    true
                });
                hashToRecordId[_hashes[i]] = recordCount;
                emit RecordSubmitted(
                    recordCount, _hashes[i], _participantIds[i],
                    _recordTypes[i], _riskScores[i], _isAnomalies[i],
                    block.timestamp
                );
            }
        }
    }

    // ─────────────────────────────────────────────
    // READ FUNCTIONS
    // ─────────────────────────────────────────────

    /**
     * @notice Retrieve a supply chain record by ID
     */
    function getRecord(uint256 _recordId)
        external
        view
        returns (SupplyChainRecord memory)
    {
        require(_recordId > 0 && _recordId <= recordCount, "SCM: Invalid record ID");
        return records[_recordId];
    }

    /**
     * @notice Verify if a hash exists and retrieve its record ID
     */
    function verifyHash(bytes32 _hash)
        external
        view
        returns (bool exists, uint256 recordId)
    {
        recordId = hashToRecordId[_hash];
        exists = recordId != 0;
    }

    /**
     * @notice Get risk score for a record (returns actual float ÷ 100)
     */
    function getRiskScore(uint256 _recordId)
        external
        view
        returns (uint16 scaledScore, string memory riskLevel)
    {
        require(_recordId > 0 && _recordId <= recordCount, "SCM: Invalid record ID");
        scaledScore = records[_recordId].riskScore;

        if (scaledScore >= 8000)      riskLevel = "CRITICAL";
        else if (scaledScore >= 6000) riskLevel = "HIGH";
        else if (scaledScore >= 4000) riskLevel = "MEDIUM";
        else                          riskLevel = "LOW";
    }

    /**
     * @notice Get recent records (pagination support for dashboard)
     */
    function getRecentRecords(uint256 _count)
        external
        view
        returns (SupplyChainRecord[] memory)
    {
        uint256 count = _count > recordCount ? recordCount : _count;
        SupplyChainRecord[] memory result = new SupplyChainRecord[](count);
        for (uint256 i = 0; i < count; i++) {
            result[i] = records[recordCount - i];
        }
        return result;
    }

    // ─────────────────────────────────────────────
    // ADMIN FUNCTIONS
    // ─────────────────────────────────────────────

    function authorizeNode(address _node, string calldata _participantId)
        external onlyOwner
    {
        authorizedNodes[_node] = true;
        nodeParticipantId[_node] = _participantId;
        emit NodeAuthorized(_node, _participantId);
    }

    function revokeNode(address _node) external onlyOwner {
        authorizedNodes[_node] = false;
        emit NodeRevoked(_node);
    }

    function updatePBFTCoordinator(address _newCoordinator)
        external onlyOwner
    {
        pbftCoordinator = _newCoordinator;
        emit PBFTCoordinatorUpdated(_newCoordinator);
    }

    function getContractInfo()
        external
        view
        returns (
            address contractOwner,
            address coordinator,
            uint256 totalRecords,
            uint256 currentBlock
        )
    {
        return (owner, pbftCoordinator, recordCount, block.number);
    }
}

"""
=============================================================================
PHASE 4: INTEROPERABILITY LAYER — FastAPI Bridge
=============================================================================
This module bridges the off-chain AI/ML world with the on-chain Ethereum world.

Architecture:
  Python ML Model (off-chain)
      ↓  [SHA-256 Hash]
  FastAPI REST Server
      ↓  [Web3.py / ethers.js]
  Ethereum Node (Ganache/Sepolia)
      ↓
  SecureSupplyChain Smart Contract

Install: pip install fastapi uvicorn web3 python-dotenv pydantic
Run:     uvicorn blockchain_bridge:app --reload --port 8000
=============================================================================
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
import hashlib
import json
import time
import os
import asyncio
from datetime import datetime


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

# ⚠️ In production, load from environment variables / .env file
GANACHE_URL        = os.getenv("WEB3_PROVIDER_URL", "http://127.0.0.1:7545")
SEPOLIA_URL        = os.getenv("SEPOLIA_URL", "https://sepolia.infura.io/v3/YOUR_INFURA_KEY")
CONTRACT_ADDRESS   = os.getenv("CONTRACT_ADDRESS", "0xe78A0F7E598Cc8b0Bb87894B0F60dD2a88d6a8Ab")
DEPLOYER_ACCOUNT   = os.getenv("DEPLOYER_ACCOUNT", "0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1")
PRIVATE_KEY        = os.getenv("PRIVATE_KEY", "0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d")  # Never hardcode in prod!

# Contract ABI (paste full ABI from Remix/Hardhat compilation)
CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32",  "name": "_dataHash",      "type": "bytes32"},
            {"internalType": "string",   "name": "_participantId", "type": "string"},
            {"internalType": "string",   "name": "_recordType",    "type": "string"},
            {"internalType": "uint16",   "name": "_riskScore",     "type": "uint16"},
            {"internalType": "bool",     "name": "_isAnomaly",     "type": "bool"},
        ],
        "name": "submitRecord",
        "outputs": [{"internalType": "uint256", "name": "recordId", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_recordId", "type": "uint256"}],
        "name": "getRecord",
        "outputs": [
            {
                "components": [
                    {"internalType": "bytes32", "name": "dataHash",      "type": "bytes32"},
                    {"internalType": "string",  "name": "participantId", "type": "string"},
                    {"internalType": "string",  "name": "recordType",    "type": "string"},
                    {"internalType": "uint16",  "name": "riskScore",     "type": "uint16"},
                    {"internalType": "bool",    "name": "isAnomaly",     "type": "bool"},
                    {"internalType": "uint256", "name": "timestamp",     "type": "uint256"},
                    {"internalType": "uint256", "name": "blockNumber",   "type": "uint256"},
                    {"internalType": "bool",    "name": "isVerified",    "type": "bool"},
                ],
                "internalType": "struct SecureSupplyChain.SupplyChainRecord",
                "name": "",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "_hash", "type": "bytes32"}],
        "name": "verifyHash",
        "outputs": [
            {"internalType": "bool",    "name": "exists",   "type": "bool"},
            {"internalType": "uint256", "name": "recordId", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "_count", "type": "uint256"}],
        "name": "getRecentRecords",
        "outputs": [],  # simplified — paste full from Remix
        "stateMutability": "view",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True,  "internalType": "uint256", "name": "recordId",     "type": "uint256"},
            {"indexed": True,  "internalType": "bytes32", "name": "dataHash",     "type": "bytes32"},
            {"indexed": False, "internalType": "string",  "name": "participantId","type": "string"},
            {"indexed": False, "internalType": "string",  "name": "recordType",   "type": "string"},
            {"indexed": False, "internalType": "uint16",  "name": "riskScore",    "type": "uint16"},
            {"indexed": False, "internalType": "bool",    "name": "isAnomaly",    "type": "bool"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp",    "type": "uint256"},
        ],
        "name": "RecordSubmitted",
        "type": "event",
    },
]


# ─────────────────────────────────────────────
# WEB3 INITIALIZATION
# ─────────────────────────────────────────────

def get_web3_connection(network: str = "ganache") -> Web3:
    """Initialize Web3 connection to Ganache (local) or Sepolia (testnet)."""
    url = GANACHE_URL if network == "ganache" else SEPOLIA_URL
    w3 = Web3(Web3.HTTPProvider(url))

    # Required for PoA networks (Sepolia, Ganache)
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    if not w3.is_connected():
        raise ConnectionError(f"Cannot connect to {network} at {url}")

    print(f"[WEB3] Connected to {network} | Block: {w3.eth.block_number}")
    return w3


def get_contract(w3: Web3):
    """Get contract instance."""
    checksum_addr = Web3.to_checksum_address(CONTRACT_ADDRESS)
    return w3.eth.contract(address=checksum_addr, abi=CONTRACT_ABI)


# ─────────────────────────────────────────────
# PBFT SIMULATION (Coordinator Logic)
# ─────────────────────────────────────────────

class PBFTCoordinator:
    """
    Simplified PBFT (Practical Byzantine Fault Tolerance) Coordinator.

    In a real PBFT network (e.g., Hyperledger Besu):
      - f = number of faulty nodes tolerated
      - Total nodes N ≥ 3f + 1
      - Example: f=1 requires N≥4 nodes; f=2 requires N≥7

    3-Phase Protocol:
    ─────────────────
    1. PRE-PREPARE (Leader → Replicas)
       Leader broadcasts: <PRE-PREPARE, view v, seq n, digest d>
       Replicas verify and move to PREPARE phase.

    2. PREPARE (All Replicas broadcast)
       Each replica sends: <PREPARE, view v, seq n, digest d, node_id>
       After receiving 2f PREPARE messages → move to COMMIT

    3. COMMIT (All Replicas broadcast)
       Each replica sends: <COMMIT, view v, seq n, digest d, node_id>
       After receiving 2f+1 COMMIT messages → EXECUTE (call smart contract)

    This class simulates the coordinator's role in collecting votes.
    """

    def __init__(self, total_nodes: int = 4, faulty_nodes: int = 1):
        self.n = total_nodes
        self.f = faulty_nodes
        self.required_prepare = 2 * faulty_nodes       # 2f PREPARE messages
        self.required_commit  = 2 * faulty_nodes + 1   # 2f+1 COMMIT messages
        self.view = 0
        self.sequence = 0
        print(f"[PBFT] Network: {total_nodes} nodes, fault tolerance: f={faulty_nodes}")
        print(f"[PBFT] Required PREPARE: {self.required_prepare}, COMMIT: {self.required_commit}")

    def pre_prepare(self, data_hash: str, payload: dict) -> dict:
        """Phase 1: Leader broadcasts the transaction."""
        self.sequence += 1
        message = {
            "phase": "PRE-PREPARE",
            "view": self.view,
            "sequence": self.sequence,
            "digest": data_hash,
            "payload": payload,
            "leader": "NODE_0",
            "timestamp": time.time()
        }
        print(f"[PBFT] PRE-PREPARE | Seq={self.sequence} | Hash={data_hash[:16]}...")
        return message

    def prepare_phase(self, pre_prepare_msg: dict) -> dict:
        """Phase 2: Simulate replica PREPARE votes."""
        votes = []
        for node_id in range(1, self.n):  # All non-leader nodes
            # Simulate: honest nodes send PREPARE, Byzantine nodes may not
            if node_id <= self.n - self.f - 1:  # Honest nodes
                votes.append({
                    "phase": "PREPARE",
                    "node_id": f"NODE_{node_id}",
                    "digest": pre_prepare_msg["digest"],
                    "view": pre_prepare_msg["view"],
                    "sequence": pre_prepare_msg["sequence"]
                })

        prepared = len(votes) >= self.required_prepare
        print(f"[PBFT] PREPARE | Votes={len(votes)}/{self.required_prepare} | Prepared={prepared}")
        return {"prepared": prepared, "votes": votes}

    def commit_phase(self, prepare_result: dict) -> dict:
        """Phase 3: Simulate COMMIT votes after PREPARE success."""
        if not prepare_result["prepared"]:
            return {"committed": False, "reason": "PREPARE phase failed"}

        commits = []
        for node_id in range(self.n):
            if node_id <= self.n - self.f - 1:
                commits.append({
                    "phase": "COMMIT",
                    "node_id": f"NODE_{node_id}",
                    "status": "COMMITTED"
                })

        committed = len(commits) >= self.required_commit
        print(f"[PBFT] COMMIT | Votes={len(commits)}/{self.required_commit} | Committed={committed}")
        return {"committed": committed, "commits": commits}

    def run_consensus(self, data_hash: str, payload: dict) -> bool:
        """Run full 3-phase PBFT consensus. Returns True if committed."""
        print(f"\n[PBFT] Starting consensus for hash {data_hash[:16]}...")
        pp_msg = self.pre_prepare(data_hash, payload)
        prep_result = self.prepare_phase(pp_msg)
        commit_result = self.commit_phase(prep_result)
        success = commit_result.get("committed", False)
        print(f"[PBFT] Consensus result: {'✓ COMMITTED' if success else '✗ FAILED'}")
        return success


# ─────────────────────────────────────────────
# FASTAPI APPLICATION
# ─────────────────────────────────────────────

app = FastAPI(
    title="Secure Supply Chain — Blockchain Bridge",
    description="FastAPI bridge connecting AI/ML pipeline to Ethereum blockchain via PBFT consensus",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pbft = PBFTCoordinator(total_nodes=4, faulty_nodes=1)


# ─────────────────────────────────────────────
# PYDANTIC MODELS
# ─────────────────────────────────────────────

class MLPredictionInput(BaseModel):
    transaction_id: str = Field(..., description="Unique order/transaction ID")
    participant_id: str = Field(..., description="Supplier, logistics node, or retailer ID")
    rf_prediction: int = Field(..., ge=0, le=1, description="0=on-time, 1=late delivery")
    rf_confidence: float = Field(..., ge=0.0, le=1.0)
    anomaly_score: float = Field(..., description="Isolation Forest decision score")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Attention-weighted risk 0–100")
    is_anomaly: bool = Field(..., description="True if flagged as fraudulent/anomalous")
    record_type: str = Field("PREDICTION", description="PREDICTION | ANOMALY | SHIPMENT")
    metadata: Optional[dict] = None


class BlockchainResponse(BaseModel):
    success: bool
    transaction_hash: Optional[str]
    record_id: Optional[int]
    data_hash: str
    pbft_committed: bool
    gas_used: Optional[int]
    block_number: Optional[int]
    message: str


class RecordResponse(BaseModel):
    record_id: int
    data_hash: str
    participant_id: str
    record_type: str
    risk_score: float
    is_anomaly: bool
    is_verified: bool
    timestamp: str
    block_number: int
    risk_level: str


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def compute_sha256(payload: dict) -> str:
    """Compute SHA-256 hash of the ML payload."""
    canonical = json.dumps(payload, sort_keys=True)
    return "0x" + hashlib.sha256(canonical.encode()).hexdigest()


def hash_to_bytes32(hex_hash: str) -> bytes:
    """Convert 0x-prefixed hex hash to bytes32 for Solidity."""
    clean = hex_hash.replace("0x", "")
    return bytes.fromhex(clean)


def get_risk_level(score: float) -> str:
    if score >= 80: return "CRITICAL"
    elif score >= 60: return "HIGH"
    elif score >= 40: return "MEDIUM"
    return "LOW"


# ─────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "Secure Supply Chain Bridge",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Check Web3 connection and contract status."""
    try:
        w3 = get_web3_connection()
        contract = get_contract(w3)
        info = contract.functions.getContractInfo().call()
        return {
            "web3_connected": True,
            "network": "ganache",
            "block_number": w3.eth.block_number,
            "contract_address": CONTRACT_ADDRESS,
            "total_records": info[2],
            "pbft_nodes": pbft.n,
        }
    except Exception as e:
        return {"web3_connected": False, "error": str(e)}


@app.post("/submit", response_model=BlockchainResponse, tags=["Core"])
async def submit_ml_prediction(data: MLPredictionInput):
    """
    Main endpoint: Receives ML prediction, runs PBFT consensus, records on blockchain.

    Flow:
    1. Receive ML data from Python pipeline
    2. Compute SHA-256 hash
    3. Run PBFT consensus (3-phase)
    4. On consensus success → submit to smart contract
    5. Return transaction hash + record ID
    """
    # Step 1: Build payload
    payload = {
        "transaction_id": data.transaction_id,
        "rf_prediction": data.rf_prediction,
        "rf_confidence": round(data.rf_confidence, 6),
        "anomaly_score": round(data.anomaly_score, 6),
        "risk_score": round(data.risk_score, 4),
        "timestamp": int(time.time()),
        "metadata": data.metadata or {}
    }

    # Step 2: SHA-256 fingerprint
    data_hash = compute_sha256(payload)
    print(f"\n[BRIDGE] New submission | TX: {data.transaction_id} | Hash: {data_hash[:20]}...")

    # Step 3: PBFT Consensus
    pbft_committed = pbft.run_consensus(data_hash, payload)
    if not pbft_committed:
        raise HTTPException(
            status_code=503,
            detail="PBFT consensus failed — transaction not committed"
        )

    # Step 4: Submit to Ethereum
    try:
        w3 = get_web3_connection()
        contract = get_contract(w3)
        account = Web3.to_checksum_address(DEPLOYER_ACCOUNT)

        risk_score_scaled = int(data.risk_score * 100)  # e.g., 75.50 → 7550
        hash_bytes32 = hash_to_bytes32(data_hash)

        # Build transaction
        txn = contract.functions.submitRecord(
            hash_bytes32,
            data.participant_id,
            data.record_type,
            risk_score_scaled,
            data.is_anomaly
        ).build_transaction({
            "from": account,
            "nonce": w3.eth.get_transaction_count(account),
            "gas": 200000,
            "gasPrice": w3.to_wei("20", "gwei"),
        })

        # Sign and send
        signed = w3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

        # Parse record ID from event
        record_id = None
        try:
            logs = contract.events.RecordSubmitted().process_receipt(receipt)
            if logs:
                record_id = logs[0]["args"]["recordId"]
        except Exception:
            pass

        print(f"[BRIDGE] ✓ On-chain | TX: {tx_hash.hex()} | RecordID: {record_id}")
        return BlockchainResponse(
            success=True,
            transaction_hash="0x" + tx_hash.hex(),
            record_id=record_id,
            data_hash=data_hash,
            pbft_committed=True,
            gas_used=receipt.gasUsed,
            block_number=receipt.blockNumber,
            message="Record successfully committed via PBFT and stored on blockchain"
        )

    except Exception as e:
        print(f"[BRIDGE] ✗ Blockchain error: {e}")
        raise HTTPException(status_code=500, detail=f"Blockchain submission failed: {str(e)}")


@app.get("/record/{record_id}", response_model=RecordResponse, tags=["Query"])
async def get_record(record_id: int):
    """Fetch a supply chain record from the blockchain by ID."""
    try:
        w3 = get_web3_connection()
        contract = get_contract(w3)
        rec = contract.functions.getRecord(record_id).call()
        return RecordResponse(
            record_id=record_id,
            data_hash="0x" + rec[0].hex(),
            participant_id=rec[1],
            record_type=rec[2],
            risk_score=rec[3] / 100.0,
            is_anomaly=rec[4],
            is_verified=rec[7],
            timestamp=datetime.utcfromtimestamp(rec[5]).isoformat(),
            block_number=rec[6],
            risk_level=get_risk_level(rec[3] / 100.0)
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/verify/{data_hash}", tags=["Query"])
async def verify_hash(data_hash: str):
    """Verify if a SHA-256 hash exists on the blockchain."""
    try:
        w3 = get_web3_connection()
        contract = get_contract(w3)
        hash_bytes = hash_to_bytes32(data_hash)
        exists, record_id = contract.functions.verifyHash(hash_bytes).call()
        return {
            "hash": data_hash,
            "exists_on_chain": exists,
            "record_id": record_id if exists else None,
            "message": "Hash verified on blockchain" if exists else "Hash not found"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/records/recent", tags=["Query"])
async def get_recent_records(count: int = 10):
    """Get the most recent N records from the blockchain."""
    try:
        w3 = get_web3_connection()
        contract = get_contract(w3)
        info = contract.functions.getContractInfo().call()
        total = info[2]
        result = []
        for i in range(min(count, total)):
            rec_id = total - i
            rec = contract.functions.getRecord(rec_id).call()
            result.append({
                "record_id": rec_id,
                "data_hash": "0x" + rec[0].hex()[:16] + "...",
                "participant_id": rec[1],
                "record_type": rec[2],
                "risk_score": rec[3] / 100.0,
                "is_anomaly": rec[4],
                "timestamp": datetime.utcfromtimestamp(rec[5]).isoformat(),
                "block_number": rec[6],
                "risk_level": get_risk_level(rec[3] / 100.0)
            })
        return {"total_records": total, "records": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# STARTUP
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("blockchain_bridge:app", host="0.0.0.0", port=8000, reload=True)
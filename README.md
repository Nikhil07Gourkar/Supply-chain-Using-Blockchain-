# 🔐 Multi-Layered Secure Supply Chain Framework
### Integrating AI-Driven Predictive Analytics and PBFT-based Blockchain Consensus

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Solidity](https://img.shields.io/badge/Solidity-0.8.19-363636)
![React](https://img.shields.io/badge/React-18.x-61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688)
![Ganache](https://img.shields.io/badge/Ganache-7.9.2-E4A663)
![License](https://img.shields.io/badge/License-MIT-green)

> **Final Year Engineering Project — B.E. / B.Tech Computer Science & Engineering**

---

## 📌 Overview

A full-stack secure supply chain system that combines **Machine Learning** for risk prediction and fraud detection with **Blockchain** for tamper-proof record keeping. Every ML prediction is cryptographically hashed and stored on an Ethereum blockchain after passing through a **PBFT consensus** protocol.

---

## 🔄 Complete Data Flow

```
DataCo Dataset
      ↓
Python cleans data (pandas + sklearn)
      ↓
Random Forest predicts Late Delivery Risk
      ↓
Isolation Forest detects Anomalies
      ↓
Attention Mechanism calculates Risk Score
      ↓
SHA-256 creates Digital Fingerprint
      ↓
FastAPI Bridge receives the data
      ↓
PBFT Consensus runs (4 nodes, 3 phases)
      ↓
Web3.py signs and sends transaction
      ↓
Ganache Blockchain stores the hash
      ↓
Smart Contract records it permanently
      ↓
React Dashboard displays everything live
```

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────┐
│           PHASE 1: DATA INTELLIGENCE                │
│   DataCo Dataset → Preprocessing → Random Forest    │
│   → Isolation Forest → Attention Mechanism          │
└─────────────────────────┬───────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│           PHASE 2: DATA INTEGRITY                   │
│   ML Output → SHA-256 Hash → Digital Fingerprint    │
└─────────────────────────┬───────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│           PHASE 4: FASTAPI BRIDGE                   │
│   REST API → PBFT Consensus → Web3.py Transaction   │
└─────────────────────────┬───────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│           PHASE 3: BLOCKCHAIN CORE                  │
│   Ganache Network → Smart Contract → Immutable Log  │
└─────────────────────────┬───────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│           PHASE 5: WEB DASHBOARD                    │
│   Tracking Map | AI Predictions | Chain Explorer    │
└─────────────────────────────────────────────────────┘
```

---

## ✨ Features

- 🤖 **Random Forest Classifier** — Predicts late delivery risk with 200 estimators
- 🔍 **Isolation Forest** — Detects fraudulent/anomalous transactions (5% contamination)
- 🎯 **Attention Mechanism** — Dynamically prioritizes high-risk supply chain nodes
- 🔒 **SHA-256 Hashing** — Tamper-proof digital fingerprint of every ML output
- ⛓️ **PBFT Consensus** — 4-node Byzantine fault tolerant network (tolerates f=1 faulty node)
- 📜 **Solidity Smart Contract** — Immutable on-chain storage of verified records
- 🌉 **FastAPI Bridge** — REST API connecting ML pipeline to blockchain
- 📊 **React Dashboard** — Real-time visualization with 3 interactive tabs

---

## 📁 Project Structure

```
supply-chain-project/
│
├── ml/
│   └── ml_pipeline.py          # Phase 1 & 2 — ML models + SHA-256 hashing
│
├── blockchain/
│   └── SecureSupplyChain.sol   # Phase 3 — Solidity smart contract
│
├── bridge/
│   └── blockchain_bridge.py    # Phase 4 — FastAPI + Web3.py + PBFT
│
├── dashboard/
│   └── my-dashboard/
│       └── src/
│           └── App.js          # Phase 5 — React.js dashboard
│
└── README.md
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Machine Learning | Python, scikit-learn, pandas, numpy |
| Hashing | Python hashlib (SHA-256) |
| API Bridge | FastAPI, Uvicorn, Web3.py, Pydantic |
| Blockchain | Solidity 0.8.19, Ganache, Remix IDE |
| Frontend | React.js, Tailwind CSS, Recharts |
| Version Control | Git, GitHub |

---

## ⚙️ Requirements

- Python 3.11+
- Node.js 18+
- Ganache (`npm install -g ganache`)
- MetaMask browser extension

---

## 🚀 How to Run

### Step 1 — Install Python dependencies
```bash
pip install pandas numpy scikit-learn fastapi uvicorn web3 pydantic
```

### Step 2 — Install Node dependencies
```bash
cd dashboard/my-dashboard
npm install
```

### Step 3 — Start Ganache (Terminal 1)
```bash
ganache --port 7545 --accounts 10 --deterministic --db "ganache-data"
```

### Step 4 — Deploy Smart Contract
1. Go to [remix.ethereum.org](https://remix.ethereum.org)
2. Paste `SecureSupplyChain.sol`
3. Compile with Solidity 0.8.19
4. Deploy using Dev - Ganache Provider (`http://127.0.0.1:7545`)
5. Copy the deployed contract address

### Step 5 — Update Contract Address
Open `bridge/blockchain_bridge.py` and update:
```python
CONTRACT_ADDRESS = "0xYourDeployedContractAddress"
```

### Step 6 — Start FastAPI Bridge (Terminal 2)
```bash
cd bridge
uvicorn blockchain_bridge:app --reload --port 8000
```

### Step 7 — Start Dashboard (Terminal 3)
```bash
cd dashboard/my-dashboard
npm start
```

### Step 8 — Run ML Pipeline (Terminal 4)
```bash
cd ml
python ml_pipeline.py
```

### Step 9 — Open Dashboard
```
http://localhost:3000
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check Web3 connection and contract status |
| POST | `/submit` | Submit ML prediction → PBFT → Blockchain |
| GET | `/record/{id}` | Fetch record by ID from blockchain |
| GET | `/verify/{hash}` | Verify SHA-256 hash on blockchain |
| GET | `/records/recent` | Get latest N ledger records |

---

## 📊 Key Metrics

| Metric | Value |
|---|---|
| PBFT Nodes | 4 |
| Fault Tolerance | f = 1 |
| PBFT Phases | PRE-PREPARE → PREPARE → COMMIT |
| RF Estimators | 200 trees |
| Anomaly Rate | 5% contamination |
| Hash Algorithm | SHA-256 (256-bit) |
| Chain ID | 1337 (Ganache) |

---

## 📸 Dashboard Screenshots

### 🗺️ Tab 1 — Real-Time Tracking Map
- Supply chain network with risk-colored nodes
- Red = CRITICAL, Orange = HIGH, Yellow = MEDIUM, Green = LOW
- Live network risk trend chart

### 🤖 Tab 2 — AI Predictions
- Risk distribution bar chart
- Prediction table with anomaly flags
- Filter by ALL / LATE / ON-TIME / ANOMALY

### ⛓️ Tab 3 — Blockchain Explorer
- SHA-256 Hash Verifier
- PBFT Consensus Flow diagram
- Immutable Ledger with all on-chain records

---

## 🔐 Security Features

- **SHA-256 Hashing** — Any tampering with ML output changes the hash
- **PBFT Consensus** — Tolerates 1 Byzantine (malicious) node out of 4
- **Smart Contract** — Records cannot be modified once stored on blockchain
- **Duplicate Detection** — Contract rejects replay attacks via hash mapping
- **Permissioned Network** — Only authorized nodes can write records

---

## 👨‍💻 Author

**Nikhil Gourkar**

---

> ⭐ If you found this project helpful, please give it a star on GitHub!

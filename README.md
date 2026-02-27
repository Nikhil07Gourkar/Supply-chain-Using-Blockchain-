# Secure Supply Chain Framework
## Final Year Engineering Project

## How to Run

### Requirements
- Python 3.11+
- Node.js 18+
- Ganache (npm install -g ganache)

### Steps
1. Start Ganache:
   ganache --port 7545 --accounts 10 --deterministic

2. Start API Bridge:
   cd bridge
   uvicorn blockchain_bridge:app --reload --port 8000

3. Start Dashboard:
   cd dashboard/my-dashboard
   npm start

4. Open browser: http://localhost:3000

## Project Structure
ml/              - Machine Learning Pipeline (Phase 1 & 2)
blockchain/      - Solidity Smart Contract (Phase 3)
bridge/          - FastAPI Blockchain Bridge (Phase 4)
dashboard/       - React.js Dashboard (Phase 5)

## Tech Stack
- Python, scikit-learn, FastAPI, Web3.py
- Solidity, Ganache, Ethereum
- React.js, Tailwind CSS, Recharts

"""
=============================================================================
PHASE 1: DATA INTELLIGENCE — ML PIPELINE
Project: Multi-Layered Secure Supply Chain Framework
=============================================================================
Dataset: DataCo Smart Supply Chain for Big Data Analysis
Source: https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis
=============================================================================
"""

import pandas as pd
import numpy as np
import hashlib
import json
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
# STEP 1: LOAD & INSPECT DATASET
# ─────────────────────────────────────────────

def load_and_inspect(filepath='DataCoSupplyChainDataset.csv'):
    """
    Load the DataCo Supply Chain dataset.
    Key columns used:
      - Type                  : Payment type (DEBIT, TRANSFER, CASH, PAYMENT)
      - Days for shipping (real): Actual days taken to ship
      - Days for shipment (scheduled): Scheduled shipping days
      - Delivery Status       : Advance, Late, On-time, Cancelled
      - Late_delivery_risk    : TARGET — 0 or 1
      - Category Name         : Product category
      - Order Item Quantity   : Units ordered
      - Sales per customer    : Revenue per customer
      - Order Item Total      : Total order value
      - Shipping Mode         : Standard, First Class, Second Class, Same Day
      - Latitude/Longitude    : Geolocation for risk mapping
    """
    try:
        df = pd.read_csv(filepath, encoding='latin-1')
    except FileNotFoundError:
        print("[INFO] Dataset not found. Generating synthetic demo data...")
        df = _generate_synthetic_data(n=5000)
    print(f"[INFO] Dataset loaded: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"[INFO] Target distribution:\n{df['Late_delivery_risk'].value_counts()}")
    return df


def _generate_synthetic_data(n=5000):
    """Generate synthetic supply chain data for demonstration."""
    np.random.seed(42)
    shipping_modes = ['Standard Class', 'Second Class', 'First Class', 'Same Day']
    categories = ['Electronics', 'Clothing', 'Office', 'Hardware', 'Books']
    payment_types = ['DEBIT', 'TRANSFER', 'CASH', 'PAYMENT']
    delivery_status = ['Late delivery', 'Advance shipping', 'Shipping on time', 'Shipping canceled']

    df = pd.DataFrame({
        'Type': np.random.choice(payment_types, n),
        'Days for shipping (real)': np.random.randint(1, 10, n),
        'Days for shipment (scheduled)': np.random.randint(1, 8, n),
        'Delivery Status': np.random.choice(delivery_status, n),
        'Late_delivery_risk': np.random.choice([0, 1], n, p=[0.45, 0.55]),
        'Category Name': np.random.choice(categories, n),
        'Order Item Quantity': np.random.randint(1, 50, n),
        'Sales per customer': np.random.uniform(10, 5000, n).round(2),
        'Order Item Total': np.random.uniform(10, 10000, n).round(2),
        'Shipping Mode': np.random.choice(shipping_modes, n),
        'Latitude': np.random.uniform(25.0, 48.0, n).round(4),
        'Longitude': np.random.uniform(-120.0, -70.0, n).round(4),
        'order date (DateOrders)': pd.date_range('2020-01-01', periods=n, freq='h').strftime('%m/%d/%Y %H:%M'),
        'Customer Id': np.random.randint(10000, 99999, n),
        'Order Id': np.random.randint(100000, 999999, n),
    })
    return df


# ─────────────────────────────────────────────
# STEP 2: PREPROCESSING
# ─────────────────────────────────────────────

def preprocess(df):
    """
    Preprocessing Pipeline:
    1. Handle null values
    2. Label Encoding for categorical features
    3. Feature Engineering (shipping delay delta)
    4. Feature Scaling with StandardScaler
    """
    df = df.copy()

    # 2.1 — Handle Nulls
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    categorical_cols = df.select_dtypes(include=['object']).columns
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
    df[categorical_cols] = df[categorical_cols].fillna('Unknown')
    print(f"[PREPROCESS] Nulls after fill: {df.isnull().sum().sum()}")

    # 2.2 — Feature Engineering
    df['shipping_delay_delta'] = (
        df['Days for shipping (real)'] - df['Days for shipment (scheduled)']
    )
    df['high_value_order'] = (df['Order Item Total'] > df['Order Item Total'].quantile(0.75)).astype(int)

    # 2.3 — Label Encoding
    le = LabelEncoder()
    encode_cols = ['Shipping Mode', 'Type', 'Delivery Status', 'Category Name']
    encoders = {}
    for col in encode_cols:
        if col in df.columns:
            df[col + '_enc'] = le.fit_transform(df[col].astype(str))
            encoders[col] = le

    # 2.4 — Select Features
    feature_cols = [
        'Days for shipping (real)',
        'Days for shipment (scheduled)',
        'shipping_delay_delta',
        'Order Item Quantity',
        'Sales per customer',
        'Order Item Total',
        'high_value_order',
        'Shipping Mode_enc',
        'Type_enc',
        'Delivery Status_enc',
        'Category Name_enc',
    ]
    feature_cols = [c for c in feature_cols if c in df.columns]
    X = df[feature_cols]
    y = df['Late_delivery_risk']

    # 2.5 — Scale
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_scaled = pd.DataFrame(X_scaled, columns=feature_cols)

    print(f"[PREPROCESS] Features: {feature_cols}")
    print(f"[PREPROCESS] X shape: {X_scaled.shape}, y distribution: {dict(y.value_counts())}")
    return X_scaled, y, scaler, encoders, feature_cols


# ─────────────────────────────────────────────
# STEP 3: RANDOM FOREST — PREDICTIVE MODEL
# ─────────────────────────────────────────────

def train_random_forest(X_scaled, y):
    """
    Random Forest Classifier to predict Late Delivery Risk.
    Hyperparameters chosen for supply chain use:
      - n_estimators=200   : Ensemble size for stable predictions
      - max_depth=10       : Prevent overfitting on noisy logistics data
      - class_weight=balanced: Handle class imbalance
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )

    rf_model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    rf_model.fit(X_train, y_train)

    y_pred = rf_model.predict(X_test)
    y_prob = rf_model.predict_proba(X_test)[:, 1]

    print("\n[RANDOM FOREST] Classification Report:")
    print(classification_report(y_test, y_pred))
    print(f"[RANDOM FOREST] ROC-AUC Score: {roc_auc_score(y_test, y_prob):.4f}")
    print(f"[RANDOM FOREST] Feature Importances (Top 5):")
    importances = pd.Series(rf_model.feature_importances_, index=X_scaled.columns)
    print(importances.nlargest(5))

    return rf_model, X_test, y_test, y_pred, y_prob


# ─────────────────────────────────────────────
# STEP 4: ISOLATION FOREST — ANOMALY / FRAUD DETECTION
# ─────────────────────────────────────────────

def train_isolation_forest(X_scaled):
    """
    Isolation Forest for unsupervised anomaly detection.
    Identifies fraudulent transactions or data anomalies:
      - Unusual order quantities
      - Abnormal shipping delays
      - Suspicious financial patterns

    contamination=0.05: ~5% of supply chain transactions are anomalous
    """
    iso_forest = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        max_samples='auto',
        random_state=42,
        n_jobs=-1
    )
    iso_forest.fit(X_scaled)

    anomaly_labels = iso_forest.predict(X_scaled)   # -1 = anomaly, 1 = normal
    anomaly_scores = iso_forest.decision_function(X_scaled)  # Lower = more anomalous

    n_anomalies = (anomaly_labels == -1).sum()
    print(f"\n[ISOLATION FOREST] Anomalies detected: {n_anomalies} / {len(X_scaled)}")
    print(f"[ISOLATION FOREST] Anomaly rate: {n_anomalies/len(X_scaled)*100:.2f}%")
    print(f"[ISOLATION FOREST] Score range: [{anomaly_scores.min():.4f}, {anomaly_scores.max():.4f}]")

    return iso_forest, anomaly_labels, anomaly_scores


# ─────────────────────────────────────────────
# STEP 5: ATTENTION MECHANISM — HIGH-RISK NODE PRIORITIZATION
# ─────────────────────────────────────────────

def compute_attention_weights(rf_model, X_scaled, anomaly_scores, feature_cols):
    """
    Simplified Attention Mechanism for Supply Chain Risk Prioritization.

    Concept:
    --------
    Standard ML treats all features equally at inference time.
    Attention weights dynamically re-weight feature importance based on:
      1. Global feature importance (from Random Forest)
      2. Local anomaly severity (from Isolation Forest scores)
      3. Composite attention score → identifies HIGH-RISK supplier/logistics nodes

    Formula:
      attention_i = softmax(feature_importance * anomaly_severity_i)
      risk_score_i = sum(attention_i * X_i)

    This is analogous to the key-query-value mechanism in transformer attention,
    adapted for tabular supply chain data.
    """
    # Global feature importance as "query weights"
    feat_importance = rf_model.feature_importances_

    # Normalize anomaly scores to [0, 1] — higher means MORE anomalous
    norm_anomaly = (anomaly_scores - anomaly_scores.min()) / (anomaly_scores.max() - anomaly_scores.min() + 1e-8)
    norm_anomaly = 1 - norm_anomaly  # Invert: low decision score = high anomaly severity

    # Attention weights: feature_importance scaled by per-row anomaly severity
    X_array = X_scaled.values
    attention_weights = np.outer(norm_anomaly, feat_importance)

    # Softmax normalization per row
    def softmax(x):
        e_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return e_x / e_x.sum(axis=1, keepdims=True)

    attention_weights = softmax(attention_weights)

    # Composite risk score per transaction
    attended_features = attention_weights * X_array
    composite_risk_score = attended_features.sum(axis=1)

    # Normalize to [0, 100]
    risk_score_normalized = (
        (composite_risk_score - composite_risk_score.min()) /
        (composite_risk_score.max() - composite_risk_score.min() + 1e-8)
    ) * 100

    print(f"\n[ATTENTION] High-risk nodes (score > 80): {(risk_score_normalized > 80).sum()}")
    print(f"[ATTENTION] Medium-risk nodes (50-80):    {((risk_score_normalized >= 50) & (risk_score_normalized <= 80)).sum()}")
    print(f"[ATTENTION] Low-risk nodes (< 50):        {(risk_score_normalized < 50).sum()}")

    return risk_score_normalized, attention_weights


# ─────────────────────────────────────────────
# PHASE 2: SHA-256 DIGITAL FINGERPRINT
# ─────────────────────────────────────────────

def create_digital_fingerprint(transaction_id, rf_prediction, rf_confidence,
                                anomaly_score, risk_score, metadata=None):
    """
    Phase 2: Create a tamper-proof digital fingerprint of ML outputs.

    The hash encapsulates:
      - Transaction/Order ID
      - Random Forest prediction (0=on-time, 1=late)
      - Prediction confidence (probability)
      - Isolation Forest anomaly score
      - Composite attention-based risk score
      - Timestamp (Unix epoch for determinism)
      - Optional metadata (supplier ID, logistics node)

    This hash is what gets recorded on the blockchain — NOT the raw data.
    Any tampering with the ML output changes the hash, invalidating the record.
    """
    import time

    payload = {
        "transaction_id": str(transaction_id),
        "rf_prediction": int(rf_prediction),
        "rf_confidence": round(float(rf_confidence), 6),
        "anomaly_score": round(float(anomaly_score), 6),
        "risk_score": round(float(risk_score), 4),
        "timestamp": int(time.time()),
        "metadata": metadata or {}
    }

    # Canonical JSON (sorted keys for determinism)
    payload_string = json.dumps(payload, sort_keys=True)
    sha256_hash = hashlib.sha256(payload_string.encode('utf-8')).hexdigest()

    return {
        "payload": payload,
        "payload_string": payload_string,
        "sha256_hash": "0x" + sha256_hash,
    }


def batch_fingerprint(df_sample, rf_model, X_scaled, anomaly_scores, risk_scores):
    """
    Generate SHA-256 fingerprints for a batch of transactions.
    Returns a list of records ready for blockchain submission.
    """
    rf_probs = rf_model.predict_proba(X_scaled)[:, 1]
    rf_preds = rf_model.predict(X_scaled)

    records = []
    for i in range(min(5, len(df_sample))):  # Demo: first 5 records
        order_id = df_sample.get('Order Id', pd.Series(range(1000))).iloc[i] \
                   if hasattr(df_sample, 'get') else i + 1000
        fingerprint = create_digital_fingerprint(
            transaction_id=order_id,
            rf_prediction=rf_preds[i],
            rf_confidence=rf_probs[i],
            anomaly_score=float(anomaly_scores[i]),
            risk_score=float(risk_scores[i]),
            metadata={"node_type": "logistics", "region": "US-WEST"}
        )
        records.append(fingerprint)
        print(f"\n[FINGERPRINT] Order {order_id}")
        print(f"  Prediction : {'LATE' if rf_preds[i] else 'ON-TIME'} ({rf_probs[i]*100:.1f}% confidence)")
        print(f"  Risk Score : {risk_scores[i]:.1f}/100")
        print(f"  SHA-256    : {fingerprint['sha256_hash'][:20]}...{fingerprint['sha256_hash'][-8:]}")

    return records


# ─────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  SECURE SUPPLY CHAIN — ML PIPELINE")
    print("=" * 60)

    # Phase 1: Data
    df = load_and_inspect()
    X_scaled, y, scaler, encoders, feature_cols = preprocess(df)

    # Phase 1: Models
    rf_model, X_test, y_test, y_pred, y_prob = train_random_forest(X_scaled, y)
    iso_model, anomaly_labels, anomaly_scores = train_isolation_forest(X_scaled)

    # Phase 1: Attention
    risk_scores, attention_weights = compute_attention_weights(
        rf_model, X_scaled, anomaly_scores, feature_cols
    )

    # Phase 2: Fingerprinting
    print("\n" + "=" * 60)
    print("  PHASE 2: SHA-256 DIGITAL FINGERPRINTS")
    print("=" * 60)
    blockchain_records = batch_fingerprint(df, rf_model, X_scaled, anomaly_scores, risk_scores)

    print("\n[DONE] Records ready for blockchain submission.")
    print(f"[DONE] Total blockchain-ready records: {len(blockchain_records)}")

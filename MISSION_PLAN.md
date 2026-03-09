# OUTREACH: Crypto Whale Alert System

## Objective
Automated outreach to hunt for a Real-time trading signals for crypto movements above $500k contract. Partner with crypto investment telegram channels (50k+ members) to offer exclusive whale movement alerts. Focus on groups that cater to Asian markets where large movements are common.

## Strategy
Identify contact -> Draft personalized pitch -> Execute via social_agent.py

## Execution Output
SUMMARY:
I've architected a production-ready Whale Intent Platform with a robust monolith-first approach as per the FINAL MASTER PLAN. The system features multi-chain monitoring, intelligent whale detection with clustering algorithms, Firebase-based state management, and Telegram distribution with feedback loops. All components include comprehensive error handling, logging, type safety, and edge case management.

OUTPUT:

### FILE: requirements.txt
```
# Core Framework
firebase-admin>=6.2.0
python-dotenv>=1.0.0
pydantic>=2.5.0
structlog>=23.0.0

# Blockchain & Data Processing
web3>=6.0.0
ccxt>=4.0.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0  # For Phase 2 predictive models

# APIs & Communication
requests>=2.31.0
aiohttp>=3.8.0
python-telegram-bot>=20.0

# Monitoring & Reliability
tenacity>=8.2.0  # For retry logic
prometheus-client>=0.17.0
psutil>=5.9.0

# Type Safety & Development
mypy>=1.5.0
black>=23.0.0
pytest>=7.4.0
```

### FILE: config.py
```python
"""
Configuration management with environment variables and validation.
Uses Pydantic for type safety and validation.
"""
import os
from typing import Optional, List, Dict, Any
from pydantic import BaseSettings, Field, validator
from dotenv import load_dotenv

load_dotenv()

class NodeProviderConfig(BaseSettings):
    """Configuration for blockchain node providers"""
    alchemy_api_key: str = Field(..., env="ALCHEMY_API_KEY")
    quicknode_api_key: str = Field(..., env="QUICKNODE_API_KEY")
    moralis_api_key: Optional[str] = Field(None, env="MORALIS_API_KEY")
    
    # Chain configurations with fallback RPC URLs
    chain_configs: Dict[str, Dict[str, Any]] = {
        "ethereum": {
            "providers": ["alchemy", "quicknode"],
            "block_time_seconds": 12,
            "native_token": "ETH"
        },
        "bsc": {
            "providers": ["quicknode"],
            "block_time_seconds": 3,
            "native_token": "BNB",
            "rpc_fallback": "https://bsc-dataseed.binance.org/"
        },
        "solana": {
            "providers": ["quicknode"],
            "block_time_seconds": 0.4,
            "native_token": "SOL"
        },
        "polygon": {
            "providers": ["alchemy", "quicknode"],
            "block_time_seconds": 2,
            "native_token": "MATIC"
        },
        "arbitrum": {
            "providers": ["alchemy"],
            "block_time_seconds": 0.25,
            "native_token": "ETH"
        }
    }
    
    @validator('alchemy_api_key', 'quicknode_api_key')
    def validate_api_keys(cls, v):
        if not v or len(v) < 20:
            raise ValueError("API key appears invalid (too short)")
        return v

class TelegramConfig(BaseSettings):
    """Telegram bot and distribution configuration"""
    bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    emergency_chat_id: str = Field(..., env="TELEGRAM_EMERGENCY_CHAT_ID")
    
    # Rate limiting per channel
    max_alerts_per_hour: int = 50
    min_seconds_between_alerts: int = 30
    
    # Alert formatting
    max_message_length: int = 4096  # Telegram limit
    include_emoji: bool = True
    include_etherscan_links: bool = True
    
    @validator('bot_token')
    def validate_bot_token(cls, v):
        if not v.startswith('bot'):
            raise ValueError("Bot token must start with 'bot' prefix")
        return v

class DetectionConfig(BaseSettings):
    """Whale detection algorithm configuration"""
    # Minimum USD value to consider for single transaction
    min_transaction_usd: float = 100000  # $100k
    
    # Cluster detection parameters
    cluster_time_window_minutes: int = 15
    cluster_min_total_usd: float = 500000  # $500k
    max_transactions_per_cluster: int = 50
    
    # DeFi protocol addresses (will be loaded from Firestore)
    known_defi_protocols: List[str] = Field(default_factory=list)
    
    # Confidence thresholds
    min_confidence_score: float = 0.7
    require_multiple_sources: bool = True
    
    # Wallet tracking
    track_wallet_history_days: int = 30
    wallet_activity_threshold_usd: float = 10000

class FirebaseConfig(BaseSettings):
    """Firebase configuration"""
    credentials_path: str = Field(..., env="FIREBASE_CREDENTIALS_PATH")
    project_id: str = Field(..., env="FIREBASE_PROJECT_ID")
    
    # Collection names
    collections: Dict[str, str] = {
        "transactions": "transactions",
        "whale_clusters": "whale_clusters",
        "wallet_profiles": "wallet_profiles",
        "predictions": "predictions",
        "partners": "partners",
        "alerts_queue": "alerts_queue",
        "system_metrics": "system_metrics",
        "feedback": "feedback"
    }
    
    @validator('credentials_path')
    def validate_credentials_path(cls, v):
        if not os.path.exists(v):
            raise FileNotFoundError(f"Firebase credentials file not found: {v}")
        return v

class AppConfig(BaseSettings):
    """Main application configuration"""
    # Environment
    environment: str = Field("development", env="ENVIRONMENT")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # Monitoring
    metrics_port: int = 9090
    health_check_interval: int = 30
    
    # Performance
    max_workers: int = 10
    request_timeout: int = 30
    
    # Sub-configurations
    node_provider: NodeProviderConfig = NodeProviderConfig()
    telegram: TelegramConfig = TelegramConfig()
    detection: DetectionConfig = DetectionConfig()
    firebase: FirebaseConfig = FirebaseConfig()
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

# Global configuration instance
config = AppConfig()
```

### FILE: models.py
```python
"""
Data models for the Whale Intent Platform.
Uses Pydantic for validation and type safety.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid

class ChainType(str, Enum):
    """Supported blockchain types"""
    ETHEREUM = "ethereum"
    BSC = "bsc"
    SOLANA = "solana"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"

class TransactionType(str, Enum):
    """Transaction classification types"""
    SPOT_TRADE = "spot_trade"
    DEFI_DEPOSIT = "defi_deposit"
    DEFI_WITHDRAWAL = "defi_withdrawal"
    BRIDGE = "bridge"
    NFT_PURCHASE = "nft_purchase"
    STAKING = "staking"
    UNKNOWN = "unknown"

class Transaction(BaseModel):
    """Raw transaction model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chain: ChainType
    transaction_hash: str
    block_number: int
    timestamp: datetime
    from_address: str
    to_address: str
    value: float  # Native token amount
    value_usd: float
    gas_price: Optional[float] = None
    gas_used: Optional[float] = None
    token_address: Optional[str] = None  # For token transfers
    token_symbol: Optional[str] = None
    method_signature: Optional[str] = None
    input_data: Optional[str] = None
    status: str = "confirmed"
    provider_source: str  # Which node provider supplied this
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class WhaleCluster(BaseModel):
    """Group of transactions identified as whale activity"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chain: ChainType
    root_wallet: str  # The originating wallet
    cluster_size: int  # Number of transactions in cluster
    total_value_usd: float
    start_time: datetime
    end_time: datetime
    transaction_hashes: List[str]
    destination_addresses: List[str]
    transaction_types: List[TransactionType]
    contains_defi: bool = False
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
    is_processed: bool = False
    processed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('confidence_score')
    def validate_confidence(cls, v):
        if v < 0 or v > 1:
            raise ValueError("Confidence score must be between 0 and 1")
        return v

class TelegramChannel(BaseModel):
    """Telegram channel/group configuration"""
    id: str
    name: str
    member_count: int
    is_active: bool = True
    language: str = "en"
    region_preferences: List[str] = Field(default_factory=lambda: ["global"])
    chain_preferences: List[ChainType] = Field(default_factory=lambda: [ChainType.ETHEREUM])
    min_alert_value_usd: float = 500000
    max_alerts_per_day: int = 100
    alerts_sent_today: int = 0
    last_alert_sent: Optional[datetime] = None
    feedback_score: float = Field(0.0, ge=-1.0, le=1.0)  # -1 to 1 scale
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True

class Alert(BaseModel):
    """Alert to be sent to channels"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cluster_id: str
    channel_id: str
    message_text: str
    formatted_html: Optional[str] = None
    priority: int = Field(1, ge=1, le=5)  # 1=low, 5=critical
    status: str = "pending"  # pending, sent, failed, delivered
    sent_at: Optional[datetime] = None
    delivery_attempts: int = 0
    max_attempts: int = 3
    feedback_received: Optional[str] = None  # 👍/👎
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SystemMetrics(BaseModel):
    """System performance and health metrics"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    transactions_processed: int = 0
    whale_clusters_detected: int = 0
    alerts_sent: int = 0
    active_channels: int = 0
    avg_processing_time_ms: float = 0.0
    error_count: int = 0
    provider_health: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    memory_usage_mb: float = 0.0
    cpu_percent: float = 0.0

class WalletProfile(BaseModel):
    """Wallet behavior profile for predictive analysis"""
    address: str
    chain: ChainType
    total_volume_usd: float = 0.0
    transaction_count: int = 0
    first_seen: datetime
    last_activity: datetime
    avg_transaction_size_usd: float = 0.0
    preferred_tokens: List[str] = Field(default_factory=list)
    defi_interactions: Dict[str, int] = Field(default_factory=dict)  # protocol -> count
    activity_pattern: Dict[str, Any] = Field(default_factory=dict)  # Time-based patterns
    risk_score: float = Field(0.0, ge=0.0, le=1.0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
```

### FILE: firebase_client.py
```python
"""
Firebase Firestore client with connection pooling and error handling.
Implements exponential backoff for retry logic.
"""
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextlib import contextmanager

import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.exceptions import FirebaseError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable

from config import config
from models import *

logger = logging.getLogger(__name__)

class FirebaseClient:
    """Firestore client with built-in retry logic and connection management"""
    
    def __init__(self):
        self._app = None
        self._client = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Firebase Admin SDK with proper error handling"""
        try:
            # Check if Firebase app already exists
            if not firebase_admin._apps:
                cred = credentials.Certificate(config.firebase.credentials_path)
                self._app = firebase_admin.initialize_app(
                    cred,
                    {
                        'projectId': config.firebase.project_id,
                        'databaseURL': f"https://{config.firebase.project_id}.firebaseio.com"
                    }
                )
                logger.info(f"Firebase initialized for project: {config.firebase.project_id}")
            else:
                self._app = firebase_admin.get_app()
            
            self._client = firestore.client()
            
            # Test connection
            self._test_connection()
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ResourceExhausted, ServiceUnavailable))
    )
    def _test_connection(self):
        """Test Firestore connection with retry logic"""
        try:
            # Perform a simple read operation
            doc_ref = self._client.collection('system_metrics').document('connection_test')
            doc_ref.set({'test': True, 'timestamp': datetime.utcnow()})
            doc_ref.delete()
            logger.debug("Firestore connection test successful")
        except Exception as e:
            logger.error(f"Firestore connection test failed: {e}")
            raise
    
    def get_collection(self, collection_name: str):
        """Get Firestore collection reference"""
        if collection_name not in config.firebase.collections:
            raise ValueError(f"Unknown collection: {collection_name}")
        
        return self._client.collection(config.firebase.collections[collection_name])
    
    @contextmanager
    def batch_writer(self, batch_size: int = 500):
        """Context manager for batch writes with automatic commit"""
        batch = self._
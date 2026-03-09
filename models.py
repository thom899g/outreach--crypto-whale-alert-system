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
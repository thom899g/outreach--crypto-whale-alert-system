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
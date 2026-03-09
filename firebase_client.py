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
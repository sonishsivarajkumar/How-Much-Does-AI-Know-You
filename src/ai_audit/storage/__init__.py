"""Storage module for caching and persisting audit data."""

import sqlite3
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path
import aiosqlite

from ..models import ProfileData, Inference, AuditReport, ScanSession
from ..config import settings


class AuditDatabase:
    """SQLite database for storing audit data locally."""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or (settings.data_dir / "audit_data.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """Initialize database tables."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            # Profile data table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS profile_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    username TEXT NOT NULL,
                    user_id TEXT,
                    profile_text TEXT NOT NULL,
                    metadata TEXT,  -- JSON
                    raw_data TEXT,  -- JSON
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(platform, username)
                )
            """)
            
            # Inferences table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS inferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    value TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    confidence_level TEXT NOT NULL,
                    reasoning TEXT,
                    source_platforms TEXT,  -- JSON array
                    model_used TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Audit reports table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS audit_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    platforms_analyzed TEXT,  -- JSON array
                    privacy_risk_score REAL,
                    report_data TEXT,  -- Full JSON report
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Scan sessions table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS scan_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    platforms TEXT,  -- JSON array
                    status TEXT DEFAULT 'running',
                    error_message TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            
            await db.commit()
    
    async def store_profile_data(self, profile_data: ProfileData) -> int:
        """Store profile data, returning the ID."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute("""
                INSERT OR REPLACE INTO profile_data 
                (platform, username, user_id, profile_text, metadata, raw_data, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                profile_data.platform.value,
                profile_data.username,
                profile_data.user_id,
                profile_data.profile_text,
                json.dumps(profile_data.metadata),
                json.dumps(profile_data.raw_data) if profile_data.raw_data else None,
                profile_data.collected_at.isoformat()
            ))
            
            await db.commit()
            return cursor.lastrowid
    
    async def store_inference(self, inference: Inference) -> int:
        """Store an inference, returning the ID."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute("""
                INSERT INTO inferences 
                (type, value, confidence, confidence_level, reasoning, source_platforms, model_used, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                inference.type.value,
                inference.value,
                inference.confidence,
                inference.confidence_level.value,
                inference.reasoning,
                json.dumps([p.value for p in inference.source_platforms]),
                inference.model_used,
                inference.created_at.isoformat()
            ))
            
            await db.commit()
            return cursor.lastrowid
    
    async def store_audit_report(self, report: AuditReport) -> int:
        """Store a complete audit report."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute("""
                INSERT INTO audit_reports 
                (user_id, platforms_analyzed, privacy_risk_score, report_data, generated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                report.user_id,
                json.dumps([p.value for p in report.platforms_analyzed]),
                report.privacy_risk.overall_score,
                report.json(),
                report.generated_at.isoformat()
            ))
            
            await db.commit()
            return cursor.lastrowid
    
    async def get_recent_profile_data(
        self, 
        platform: str, 
        username: str, 
        max_age_hours: int = 24
    ) -> Optional[ProfileData]:
        """Get recent profile data if available and not stale."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute("""
                SELECT platform, username, user_id, profile_text, metadata, raw_data, collected_at
                FROM profile_data 
                WHERE platform = ? AND username = ? AND collected_at > ?
                ORDER BY collected_at DESC LIMIT 1
            """, (platform, username, cutoff_time.isoformat()))
            
            row = await cursor.fetchone()
            if row:
                return ProfileData(
                    platform=row[0],
                    username=row[1],
                    user_id=row[2],
                    profile_text=row[3],
                    metadata=json.loads(row[4]) if row[4] else {},
                    raw_data=json.loads(row[5]) if row[5] else None,
                    collected_at=datetime.fromisoformat(row[6])
                )
        
        return None
    
    async def get_recent_inferences(
        self, 
        limit: int = 50,
        min_confidence: float = 0.5
    ) -> List[Inference]:
        """Get recent high-confidence inferences."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute("""
                SELECT type, value, confidence, confidence_level, reasoning, source_platforms, model_used, created_at
                FROM inferences 
                WHERE confidence >= ?
                ORDER BY created_at DESC LIMIT ?
            """, (min_confidence, limit))
            
            rows = await cursor.fetchall()
            inferences = []
            
            for row in rows:
                inferences.append(Inference(
                    type=row[0],
                    value=row[1],
                    confidence=row[2],
                    confidence_level=row[3],
                    reasoning=row[4],
                    source_platforms=json.loads(row[5]),
                    model_used=row[6],
                    created_at=datetime.fromisoformat(row[7])
                ))
            
            return inferences
    
    async def get_audit_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get audit report history."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute("""
                SELECT user_id, platforms_analyzed, privacy_risk_score, generated_at
                FROM audit_reports 
                ORDER BY generated_at DESC LIMIT ?
            """, (limit,))
            
            rows = await cursor.fetchall()
            history = []
            
            for row in rows:
                history.append({
                    "user_id": row[0],
                    "platforms_analyzed": json.loads(row[1]),
                    "privacy_risk_score": row[2],
                    "generated_at": row[3]
                })
            
            return history
    
    async def create_scan_session(self, session: ScanSession) -> int:
        """Create a new scan session."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute("""
                INSERT INTO scan_sessions (session_id, platforms, status, started_at)
                VALUES (?, ?, ?, ?)
            """, (
                session.session_id,
                json.dumps([p.value for p in session.platforms]),
                session.status,
                session.started_at.isoformat()
            ))
            
            await db.commit()
            return cursor.lastrowid
    
    async def update_scan_session(
        self, 
        session_id: str, 
        status: str, 
        error_message: Optional[str] = None
    ):
        """Update scan session status."""
        completed_at = datetime.now() if status in ["completed", "failed"] else None
        
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute("""
                UPDATE scan_sessions 
                SET status = ?, error_message = ?, completed_at = ?
                WHERE session_id = ?
            """, (
                status, 
                error_message, 
                completed_at.isoformat() if completed_at else None,
                session_id
            ))
            
            await db.commit()
    
    async def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data to manage storage."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        async with aiosqlite.connect(str(self.db_path)) as db:
            # Clean old profile data
            await db.execute("""
                DELETE FROM profile_data 
                WHERE collected_at < ?
            """, (cutoff_date.isoformat(),))
            
            # Clean old inferences
            await db.execute("""
                DELETE FROM inferences 
                WHERE created_at < ?
            """, (cutoff_date.isoformat(),))
            
            # Clean old scan sessions
            await db.execute("""
                DELETE FROM scan_sessions 
                WHERE started_at < ?
            """, (cutoff_date.isoformat(),))
            
            await db.commit()


# Global database instance
db = AuditDatabase()

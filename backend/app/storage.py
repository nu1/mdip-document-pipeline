"""Small storage boundaries; extractors do not import this module."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol
from uuid import UUID


class DocumentRepository(Protocol):
    def create(self, record: dict) -> None: ...
    def get(self, document_id: str) -> dict | None: ...
    def list_documents(self, limit: int, offset: int) -> list[dict]: ...
    def update(self, document_id: str, **changes) -> None: ...
    def replace_chunks(self, document_id: str, chunks: list[dict]) -> None: ...
    def chunks(self, document_id: str, limit: int, offset: int) -> list[dict]: ...


class FileStore(Protocol):
    def save(self, file_id: str, content: bytes) -> str: ...
    def read(self, storage_uri: str) -> bytes: ...


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LocalFileStore:
    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)

    def save(self, file_id: str, content: bytes) -> str:
        key = str(UUID(file_id))
        (self.root / key).write_bytes(content)
        return key

    def read(self, storage_uri: str) -> bytes:
        return (self.root / str(UUID(storage_uri))).read_bytes()


class SQLiteRepository:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self.connection() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY, filename TEXT NOT NULL, content_type TEXT NOT NULL,
                    storage_uri TEXT NOT NULL, status TEXT NOT NULL, processing_stage TEXT NOT NULL,
                    processed_pages INTEGER, total_pages INTEGER, extracted_data TEXT,
                    error_message TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id),
                    chunk_index INTEGER NOT NULL, text TEXT NOT NULL,
                    source_location TEXT NOT NULL, metadata TEXT NOT NULL,
                    UNIQUE(document_id, chunk_index)
                );
            ''')

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys = ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def decode(row):
        if row is None:
            return None
        result = dict(row)
        if 'extracted_data' in result:
            result['extracted_data'] = json.loads(result['extracted_data']) if result['extracted_data'] else None
        return result

    def create(self, record: dict) -> None:
        with self.connection() as db:
            db.execute('''INSERT INTO documents
                (id,filename,content_type,storage_uri,status,processing_stage,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?)''',
                (record['id'], record['filename'], record['content_type'], record['storage_uri'],
                 'queued', 'queued', now(), now()))

    def get(self, document_id: str) -> dict | None:
        with self.connection() as db:
            return self.decode(db.execute('SELECT * FROM documents WHERE id=?', (document_id,)).fetchone())

    def list_documents(self, limit: int, offset: int) -> list[dict]:
        with self.connection() as db:
            return [dict(row) for row in db.execute('''SELECT id,filename,content_type,status,
                processing_stage,processed_pages,total_pages,error_message,created_at,updated_at
                FROM documents ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?''', (limit, offset))]

    def update(self, document_id: str, **changes) -> None:
        allowed = {'status', 'processing_stage', 'processed_pages', 'total_pages', 'extracted_data', 'error_message'}
        if not changes.keys() <= allowed:
            raise ValueError('Unsupported document update')
        if 'extracted_data' in changes:
            changes['extracted_data'] = json.dumps(changes['extracted_data'], ensure_ascii=False)
        changes['updated_at'] = now()
        with self.connection() as db:
            db.execute(f"UPDATE documents SET {', '.join(key + '=?' for key in changes)} WHERE id=?",
                       (*changes.values(), document_id))

    def interrupt_abandoned(self) -> None:
        with self.connection() as db:
            db.execute('''UPDATE documents SET status='failed', processing_stage='interrupted',
                error_message='Processing interrupted by server restart. Upload the file again.', updated_at=?
                WHERE status IN ('queued','processing')''', (now(),))

    def replace_chunks(self, document_id: str, chunks: list[dict]) -> None:
        with self.connection() as db:
            db.execute('DELETE FROM document_chunks WHERE document_id=?', (document_id,))
            db.executemany('INSERT INTO document_chunks VALUES (?,?,?,?,?,?)', [
                (f"{document_id}:{c['chunk_index']}", document_id, c['chunk_index'], c['text'],
                 json.dumps(c['source_location']), json.dumps(c['metadata'])) for c in chunks])

    def chunks(self, document_id: str, limit: int, offset: int) -> list[dict]:
        with self.connection() as db:
            rows = db.execute('''SELECT * FROM document_chunks WHERE document_id=?
                ORDER BY chunk_index LIMIT ? OFFSET ?''', (document_id, limit, offset))
            return [{**dict(r), 'source_location': json.loads(r['source_location']),
                     'metadata': json.loads(r['metadata'])} for r in rows]


def init_storage(db_path: Path, originals_dir: Path) -> tuple[DocumentRepository, FileStore]:
    """Initializes persistence layer, runs database recovery, and returns protocol instances."""
    repository = SQLiteRepository(db_path)
    file_store = LocalFileStore(originals_dir)
    repository.interrupt_abandoned()
    return repository, file_store



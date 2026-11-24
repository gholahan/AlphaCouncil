"""Stream Manager - Redis-backed event buffer and SSE streaming manager for LangGraph debate runs (supports Celery worker & FastAPI process sharing)."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import redis

from src.config.settings import settings

logger = logging.getLogger(__name__)


def _sanitize_data(obj: Any) -> Any:
    """Recursively convert non-serializable objects (like LangChain messages) to strings or dicts."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _sanitize_data(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_data(item) for item in obj]
    if hasattr(obj, "content"):  # LangChain Message objects (AIMessage, HumanMessage, ToolMessage)
        return f"{type(obj).__name__}: {str(obj.content)[:300]}"
    try:
        json.dumps(obj)
        return obj
    except Exception:
        return str(obj)


class DebateRunStreamManager:
    """Manages Redis-backed event buffers, state, and sequence numbering for real-time SSE streaming across Celery and FastAPI."""

    def __init__(self):
        self._redis_client = None
        self._fallback_buffers: Dict[str, List[Dict[str, Any]]] = {}
        self._fallback_sequences: Dict[str, int] = {}
        self._fallback_states: Dict[str, Dict[str, Any]] = {}
        self._init_redis()

    def _init_redis(self):
        try:
            redis_url = settings.get_celery_broker_url or settings.REDIS_URL
            if redis_url:
                if redis_url.startswith("rediss://"):
                    clean_url = redis_url.split("?")[0]
                    self._redis_client = redis.Redis.from_url(
                        clean_url,
                        decode_responses=True,
                        ssl_cert_reqs=None,
                        socket_timeout=10.0,
                        socket_connect_timeout=10.0,
                        socket_keepalive=True,
                        retry_on_timeout=True,
                    )
                else:
                    self._redis_client = redis.Redis.from_url(
                        redis_url,
                        decode_responses=True,
                        socket_timeout=10.0,
                        socket_connect_timeout=10.0,
                        socket_keepalive=True,
                        retry_on_timeout=True,
                    )
                self._redis_client.ping()
                logger.info("[StreamManager] Connected to Redis successfully.")
            else:
                logger.warning("[StreamManager] No Redis URL configured. Falling back to in-memory buffers.")
        except Exception as e:
            logger.warning(f"[StreamManager] Failed to connect to Redis ({e}). Falling back to in-memory buffers.")
            self._redis_client = None

    def _get_redis(self):
        if not self._redis_client:
            try:
                redis_url = settings.get_celery_broker_url or settings.REDIS_URL
                if redis_url:
                    if redis_url.startswith("rediss://"):
                        clean_url = redis_url.split("?")[0]
                        self._redis_client = redis.Redis.from_url(
                            clean_url,
                            decode_responses=True,
                            ssl_cert_reqs=None,
                            socket_timeout=10.0,
                            socket_connect_timeout=10.0,
                            socket_keepalive=True,
                            retry_on_timeout=True,
                        )
                    else:
                        self._redis_client = redis.Redis.from_url(
                            redis_url,
                            decode_responses=True,
                            socket_timeout=10.0,
                            socket_connect_timeout=10.0,
                            socket_keepalive=True,
                            retry_on_timeout=True,
                        )
                    self._redis_client.ping()
            except Exception:
                pass
        return self._redis_client

    async def add_event(
        self,
        run_id: str,
        event_type: str,
        node_name: Optional[str] = None,
        originating_node: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_args: Optional[Dict[str, Any]] = None,
        tool_result: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        timestamp = datetime.now(timezone.utc).isoformat()
        sanitized_args = _sanitize_data(tool_args)
        sanitized_result = _sanitize_data(tool_result)
        sanitized_data = _sanitize_data(data)

        # Always maintain local fallback buffer as well for resilience with bounded memory eviction (max 50 runs)
        if run_id not in self._fallback_buffers:
            if len(self._fallback_buffers) >= 50:
                oldest_run = next(iter(self._fallback_buffers))
                self._fallback_buffers.pop(oldest_run, None)
                self._fallback_sequences.pop(oldest_run, None)
                self._fallback_states.pop(oldest_run, None)
            self._fallback_buffers[run_id] = []
            self._fallback_sequences[run_id] = 0

        self._fallback_sequences[run_id] += 1
        seq = self._fallback_sequences[run_id]

        event = {
            "seq": seq,
            "timestamp": timestamp,
            "run_id": run_id,
            "event_type": event_type,
            "node_name": node_name,
            "originating_node": originating_node,
            "tool_name": tool_name,
            "tool_args": sanitized_args,
            "tool_result": sanitized_result,
            "data": sanitized_data or {},
        }
        self._fallback_buffers[run_id].append(event)

        r = self._get_redis()
        if r:
            try:
                seq_key = f"debate:seq:{run_id}"
                list_key = f"debate:events:{run_id}"
                redis_seq = r.incr(seq_key)
                event["seq"] = redis_seq
                r.rpush(list_key, json.dumps(event))
                r.expire(list_key, 86400)  # 24-hour TTL eviction per run
                r.expire(seq_key, 86400)  # 24-hour TTL eviction per run
                return event
            except Exception as e:
                logger.debug(f"[StreamManager] Redis add_event error ({e}), using local buffer.")

        return event

    async def set_state(self, run_id: str, state: Dict[str, Any]):
        sanitized_state = _sanitize_data(state)
        if len(self._fallback_states) >= 50 and run_id not in self._fallback_states:
            oldest_state = next(iter(self._fallback_states))
            self._fallback_states.pop(oldest_state, None)
        self._fallback_states[run_id] = sanitized_state
        r = self._get_redis()
        if r:
            try:
                state_key = f"debate:state:{run_id}"
                r.set(state_key, json.dumps(sanitized_state), ex=86400)  # 24-hour TTL eviction per run
            except Exception as e:
                logger.debug(f"[StreamManager] Redis set_state error ({e}).")

    async def get_state(self, run_id: str) -> Optional[Dict[str, Any]]:
        r = self._get_redis()
        if r:
            try:
                state_key = f"debate:state:{run_id}"
                val = r.get(state_key)
                if val:
                    return json.loads(val)
            except Exception as e:
                logger.debug(f"[StreamManager] Redis get_state error ({e}).")
        return self._fallback_states.get(run_id)

    async def get_events_after(self, run_id: str, last_seq: int) -> List[Dict[str, Any]]:
        events = []
        r = self._get_redis()
        if r:
            try:
                list_key = f"debate:events:{run_id}"
                raw_events = r.lrange(list_key, 0, -1)
                if raw_events:
                    events = [json.loads(e) for e in raw_events]
            except Exception as e:
                logger.debug(f"[StreamManager] Redis get_events_after error ({e}).")

        # Fallback to local buffer if redis returned nothing
        if not events:
            events = self._fallback_buffers.get(run_id, [])

        return [e for e in events if e["seq"] > last_seq]

    async def get_latest_seq(self, run_id: str) -> int:
        r = self._get_redis()
        if r:
            try:
                seq_key = f"debate:seq:{run_id}"
                val = r.get(seq_key)
                if val:
                    return int(val)
            except Exception as e:
                logger.debug(f"[StreamManager] Redis get_latest_seq error ({e}).")
        return self._fallback_sequences.get(run_id, 0)


# Global singleton instance
stream_manager = DebateRunStreamManager()

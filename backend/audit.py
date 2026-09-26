"""Append-only JSON Lines audit stream (one JSON object per line)."""
import asyncio
import fcntl
import inspect
import json
import os
from contextvars import ContextVar
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from uuid import uuid4

AUDIT_PATH = Path(__file__).resolve().parents[1] / 'output/audit_trail.json'
run_id = ContextVar('audit_run_id', default=None)


def append_event(event, *, tool_name=None, args=None, result=None, stop_reason=None):
    record = {'timestamp': datetime.now(timezone.utc).isoformat(), 'run_id': run_id.get(),
              'event': event, 'tool_name': tool_name, 'args': args, 'result': result, 'stop_reason': stop_reason}
    line = (json.dumps(record, ensure_ascii=False, separators=(',', ':'))+'\n').encode()
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Append mode only; never truncate, replace, or rewrite previous entries.
    fd = os.open(AUDIT_PATH, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        view=memoryview(line)
        while view:
            written=os.write(fd,view)
            view=view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


def short_args(values):
    # Do not log arbitrary user text or guessed identifiers, which may contain PII.
    return {key: value if isinstance(value,(int,float,bool)) or value is None else {'characters':len(str(value))}
            for key,value in values.items()}


def short_result(value):
    data=value.model_dump() if hasattr(value,'model_dump') else {}
    summary={k:data[k] for k in ('status','total_matches','total_quantity') if k in data}
    if 'products' in data: summary['product_count']=len(data['products'])
    if data.get('product'): summary['product_found']=True; summary['price']=data['product'].get('price')
    if 'stock' in data: summary['stock']=data['stock'][:12]
    if 'items' in data: summary['recommendation_count']=len(data['items'])
    return summary


def audit_tool(function):
    @wraps(function)
    def wrapped(*args,**kwargs):
        arguments=inspect.signature(function).bind(*args,**kwargs)
        append_event('tool_start',tool_name=function.__name__,args=short_args(arguments.arguments))
        try:
            value=function(*args,**kwargs)
        except Exception as exc:
            append_event('tool_error',tool_name=function.__name__,result={'error_type':type(exc).__name__},stop_reason='tool_error')
            raise
        append_event('tool_result',tool_name=function.__name__,result=short_result(value))
        return value
    return wrapped


def audit_run(function):
    @wraps(function)
    async def wrapped(*args,**kwargs):
        token=run_id.set(uuid4().hex)
        try:
            append_event('run_start')
            try:
                result=await function(*args,**kwargs)
            except BaseException as exc:
                reason={'UsageLimitExceeded':'usage_limit','UnexpectedModelBehavior':'invalid_model_output',
                        'CancelledError':'cancelled_or_deadline','TimeoutError':'timeout'}.get(type(exc).__name__,'error')
                append_event('run_stop',result={'error_type':type(exc).__name__},stop_reason=reason)
                raise
            append_event('run_stop',result={'reply_characters':len(result.reply),'product_count':len(result.products)},stop_reason='completed')
            return result
        finally:
            run_id.reset(token)
    return wrapped

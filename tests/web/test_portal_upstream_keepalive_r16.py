"""Bounded internal API upstream HTTP keep-alive never shares request headers."""
from __future__ import annotations

import socket

from scripts.serve_portal import _borrow_upstream, _release_upstream


def test_pool_reuses_a_healthy_connection_without_external_network() -> None:
    key = ("http", "127.0.0.1", 54321)
    connection = _borrow_upstream(key)
    local, peer = socket.socketpair()
    try:
        connection.sock = local
        _release_upstream(key, connection, reusable=True)
        second = _borrow_upstream(key)
        assert second is connection
        second.close()
    finally:
        peer.close()


def test_pool_discards_nonreusable_connections() -> None:
    key = ("http", "127.0.0.1", 54322)
    first = _borrow_upstream(key)
    _release_upstream(key, first, reusable=False)
    second = _borrow_upstream(key)
    assert second is not first
    second.close()

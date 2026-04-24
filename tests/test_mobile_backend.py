import time

import pytest

from app.mobile_backend import ApiError, MobileBackend, RateLimitPolicy


def create_backend(rate_limit: int = 120) -> MobileBackend:
    return MobileBackend(
        jwt_secret="test-secret",
        rate_limit_policy=RateLimitPolicy(requests_per_minute=rate_limit),
    )


def test_auth_and_device_registration_flow():
    backend = create_backend()
    user = backend.register_user("alice@example.com", "password123")
    token = backend.login("alice@example.com", "password123")["access_token"]
    user_id = backend.authenticate(token)

    assert user_id == user["user_id"]

    reg = backend.register_device(user_id, "dev-ios-1", "ios", "apns-token-1")
    assert reg["registered"] is True


def test_idempotency_key_returns_same_response_for_duplicate_submit():
    backend = create_backend()
    user_id = backend.register_user("bob@example.com", "pw")["user_id"]

    first = backend.upsert_item(
        user_id=user_id,
        item_id="task-1",
        payload={"title": "Buy milk", "done": False},
        idempotency_key="idem-1",
    )
    duplicate = backend.upsert_item(
        user_id=user_id,
        item_id="task-1",
        payload={"title": "Buy milk", "done": False},
        idempotency_key="idem-1",
    )

    assert duplicate == first
    assert duplicate["version"] == 1


def test_sync_cursor_and_etag_flow():
    backend = create_backend()
    user_id = backend.register_user("sync@example.com", "pw")["user_id"]

    backend.upsert_item(user_id, "item-1", {"v": 1}, idempotency_key="k1")
    backend.upsert_item(user_id, "item-2", {"v": 2}, idempotency_key="k2")

    first_sync = backend.sync(user_id=user_id, cursor=0)
    assert len(first_sync["changes"]) == 2

    second_sync = backend.sync(user_id=user_id, cursor=first_sync["next_cursor"], etag=first_sync["etag"])
    assert second_sync["not_modified"] is True
    assert second_sync["changes"] == []


def test_sync_cursor_tracks_global_change_sequence_not_item_version():
    backend = create_backend()
    user_id = backend.register_user("cursor-seq@example.com", "pw")["user_id"]

    backend.upsert_item(user_id, "item-1", {"v": 1}, idempotency_key="s1")
    first_page = backend.sync(user_id=user_id, cursor=0, limit=1)
    assert len(first_page["changes"]) == 1
    assert first_page["changes"][0]["item_id"] == "item-1"

    backend.upsert_item(user_id, "item-2", {"v": 2}, idempotency_key="s2")
    next_page = backend.sync(user_id=user_id, cursor=first_page["next_cursor"])
    assert len(next_page["changes"]) == 1
    assert next_page["changes"][0]["item_id"] == "item-2"


def test_conflict_requires_merge_then_retry():
    backend = create_backend()
    user_id = backend.register_user("conflict@example.com", "pw")["user_id"]

    created = backend.upsert_item(user_id, "item-c", {"v": 1}, idempotency_key="k3")

    with pytest.raises(ApiError) as exc:
        backend.upsert_item(
            user_id,
            "item-c",
            {"v": 2},
            idempotency_key="k4",
            expected_version=created["version"] + 1,
        )

    assert exc.value.code == "SYNC_CONFLICT"
    assert exc.value.status == 409


def test_push_pipeline_and_duplicate_notification_protection():
    backend = create_backend()
    user_id = backend.register_user("push@example.com", "pw")["user_id"]
    backend.register_device(user_id, "dev-a1", "android", "fcm-token-a1")

    result = backend.send_push(user_id, "Hi", "body", notification_id="n1")
    duplicate = backend.send_push(user_id, "Hi", "body", notification_id="n1")

    assert result["status"] == "queued"
    assert duplicate["status"] == "duplicate_ignored"
    assert len(backend.events()) == 1


def test_rate_limit_with_retry_behavior_edge_case():
    backend = create_backend(rate_limit=2)
    user_id = backend.register_user("ratelimit@example.com", "pw")["user_id"]

    backend.sync(user_id)
    backend.sync(user_id)

    with pytest.raises(ApiError) as exc:
        backend.sync(user_id)

    assert exc.value.status == 429
    assert exc.value.details["retry_after_seconds"] == 60


def test_network_retry_simulation_duplicate_delivery():
    backend = create_backend()
    user_id = backend.register_user("retry@example.com", "pw")["user_id"]

    req = dict(user_id=user_id, item_id="retry-item", payload={"count": 1}, idempotency_key="network-1")
    first = backend.upsert_item(**req)

    # Simulate client timeout then retry with same idempotency key.
    time.sleep(0.01)
    second = backend.upsert_item(**req)

    assert first == second
    assert backend.sync(user_id)["changes"][0]["version"] == 1


def test_reused_idempotency_key_with_different_payload_rejected():
    backend = create_backend()
    user_id = backend.register_user("idem-mismatch@example.com", "pw")["user_id"]

    backend.upsert_item(
        user_id=user_id,
        item_id="idem-item",
        payload={"count": 1},
        idempotency_key="idem-shared",
    )
    with pytest.raises(ApiError) as exc:
        backend.upsert_item(
            user_id=user_id,
            item_id="idem-item",
            payload={"count": 2},
            idempotency_key="idem-shared",
        )

    assert exc.value.code == "IDEMPOTENCY_PAYLOAD_MISMATCH"
    assert exc.value.status == 409


def test_same_item_id_isolated_per_user_namespace():
    backend = create_backend()
    user_a = backend.register_user("usera@example.com", "pw")["user_id"]
    user_b = backend.register_user("userb@example.com", "pw")["user_id"]

    a_record = backend.upsert_item(user_a, "shared-item", {"owner": "a"}, idempotency_key="a-1")
    b_record = backend.upsert_item(user_b, "shared-item", {"owner": "b"}, idempotency_key="b-1")

    assert a_record["version"] == 1
    assert b_record["version"] == 1
    assert backend.sync(user_a)["changes"][0]["payload"]["owner"] == "a"
    assert backend.sync(user_b)["changes"][0]["payload"]["owner"] == "b"


def test_authenticate_rejects_tampered_signature():
    backend = create_backend()
    backend.register_user("jwt-invalid@example.com", "pw")
    token = backend.login("jwt-invalid@example.com", "pw")["access_token"]
    header_b64, payload_b64, _signature = token.split(".")
    tampered = f"{header_b64}.{payload_b64}.deadbeef"

    with pytest.raises(ApiError) as exc:
        backend.authenticate(tampered)

    assert exc.value.status == 401
    assert exc.value.code == "AUTH_INVALID_TOKEN"


def test_authenticate_rejects_expired_token():
    backend = create_backend()
    backend.register_user("jwt-expired@example.com", "pw")
    backend.token_ttl_minutes = -1
    expired = backend.login("jwt-expired@example.com", "pw")["access_token"]

    with pytest.raises(ApiError) as exc:
        backend.authenticate(expired)

    assert exc.value.status == 401
    assert exc.value.code == "AUTH_EXPIRED"

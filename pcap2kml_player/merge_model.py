"""Soft merge logic for multi-PCAP TXA/RXA sessions."""

from __future__ import annotations

from collections import defaultdict
from math import asin, cos, radians, sin, sqrt
from typing import Optional

from .data_model import CaptureRole, MergedObservation, MessageType, V2xMessage, message_identity_key

DEFAULT_TIME_WINDOW_S = 0.35
CAM_TIME_WINDOW_S = 0.25
INFRA_TIME_WINDOW_S = 0.60
VEHICLE_DISTANCE_M = 20.0
INFRA_DISTANCE_M = 80.0


def build_merge_groups(messages: list[V2xMessage]) -> dict[str, MergedObservation]:
    """Build soft merge groups and annotate messages in-place.

    The merge is intentionally conservative: it groups likely duplicate
    observations from multiple capture files, but keeps all raw messages.
    """
    for msg in messages:
        msg.merge_group_id = None
        msg.merge_confidence = None
        msg.merge_reason = None

    candidates_by_bucket: dict[tuple[object, ...], list[V2xMessage]] = defaultdict(list)
    for msg in messages:
        candidates_by_bucket[_bucket_key(msg)].append(msg)

    groups: dict[str, MergedObservation] = {}
    grouped_keys: set[tuple[str, str, str]] = set()
    merge_index = 1

    for bucket_key, bucket_messages in candidates_by_bucket.items():
        bucket_messages.sort(key=lambda item: item.timestamp)
        comparison_pool = list(bucket_messages)
        for neighbor_key in _neighbor_bucket_keys(bucket_key):
            comparison_pool.extend(candidates_by_bucket.get(neighbor_key, []))
        comparison_pool.sort(key=lambda item: item.timestamp)
        for msg in bucket_messages:
            key = message_identity_key(msg)
            if key in grouped_keys:
                continue
            observations = [msg]
            scores: list[float] = []
            reasons: list[str] = []
            for other in comparison_pool:
                other_key = message_identity_key(other)
                if other is msg or other_key in grouped_keys:
                    continue
                score, reason = score_merge_candidate(msg, other)
                if score >= 0.72:
                    observations.append(other)
                    scores.append(score)
                    reasons.append(reason)

            if len(observations) < 2:
                continue

            confidence = min(0.99, max(scores) if scores else 0.72)
            merge_id = f"merge-{merge_index:05d}"
            merge_index += 1
            canonical = _choose_canonical(observations)
            observation_keys = [message_identity_key(item) for item in observations]
            reason = "; ".join(sorted(set(reasons))) or "zeit-/positionsnah"
            for item in observations:
                item.merge_group_id = merge_id
                item.merge_confidence = confidence
                item.merge_reason = reason
                grouped_keys.add(message_identity_key(item))
            groups[merge_id] = MergedObservation(
                merge_id=merge_id,
                canonical_key=message_identity_key(canonical),
                confidence=confidence,
                reason=reason,
                observation_keys=observation_keys,
            )

    return groups


def score_merge_candidate(left: V2xMessage, right: V2xMessage) -> tuple[float, str]:
    """Score whether two messages likely represent the same observed event."""
    if left.msg_type != right.msg_type:
        return (0.0, "anderer Nachrichtentyp")

    dt = abs((left.timestamp - right.timestamp).total_seconds())
    max_dt = _time_window_for_type(left.msg_type)
    if dt > max_dt:
        return (0.0, "Zeitfenster ueberschritten")

    score = 0.25
    reasons = [f"{left.msg_type.value} innerhalb {dt * 1000:.0f} ms"]

    if _complementary_roles(left, right):
        score += 0.12
        reasons.append("TXA/RXA-komplementaer")
    elif _same_source(left, right):
        score -= 0.15
        reasons.append("gleiche Quelle")

    if left.raw_payload and right.raw_payload and left.raw_payload == right.raw_payload:
        score += 0.35
        reasons.append("Payload identisch")

    key_score, key_reason = _semantic_key_score(left, right)
    score += key_score
    if key_reason:
        reasons.append(key_reason)

    if left.station_id == right.station_id:
        score += 0.12
        reasons.append("Station gleich")

    distance = _distance_m(left, right)
    max_distance = _distance_window_for_type(left.msg_type)
    if distance is not None and distance <= max_distance:
        score += 0.12
        reasons.append(f"Position {distance:.1f} m")
    elif distance is not None and distance > max_distance:
        score -= 0.25
        reasons.append(f"Position {distance:.1f} m auseinander")

    if _speed_heading_compatible(left, right):
        score += 0.06
        reasons.append("Speed/Heading kompatibel")

    return (max(0.0, min(0.99, score)), ", ".join(reasons))


def _bucket_key(msg: V2xMessage) -> tuple[object, ...]:
    semantic = _semantic_key(msg)
    window = _time_window_for_type(msg.msg_type)
    time_bucket = int(msg.timestamp.timestamp() / window)
    return (msg.msg_type, semantic, time_bucket)


def _neighbor_bucket_keys(bucket_key: tuple[object, ...]) -> list[tuple[object, ...]]:
    if len(bucket_key) != 3:
        return []
    msg_type, semantic, time_bucket = bucket_key
    if not isinstance(time_bucket, int):
        return []
    return [
        (msg_type, semantic, time_bucket - 1),
        (msg_type, semantic, time_bucket + 1),
    ]


def _semantic_key(msg: V2xMessage) -> tuple[object, ...]:
    if msg.msg_type in {MessageType.SREM, MessageType.SSEM}:
        return (
            _coerce_int(msg.decoded_data.get("intersectionId")),
            _coerce_int(msg.decoded_data.get("requestId")),
            _coerce_int(msg.decoded_data.get("sequenceNumber")),
        )
    if msg.msg_type in {MessageType.MAPEM, MessageType.SPATEM}:
        return (
            _coerce_int(msg.decoded_data.get("intersectionId")),
            _coerce_int(msg.decoded_data.get("revision")),
        )
    if msg.msg_type == MessageType.CAM:
        station_hint = msg.decoded_data.get("stationId", msg.station_id)
        return (str(station_hint),)
    return (msg.station_id,)


def _semantic_key_score(left: V2xMessage, right: V2xMessage) -> tuple[float, str]:
    left_key = _semantic_key(left)
    right_key = _semantic_key(right)
    if left_key == right_key and any(value is not None for value in left_key):
        if left.msg_type in {MessageType.SREM, MessageType.SSEM}:
            return (0.38, "Request-Key gleich")
        if left.msg_type in {MessageType.MAPEM, MessageType.SPATEM}:
            return (0.30, "Intersection/Revision gleich")
        return (0.18, "semantischer Key gleich")
    if left.msg_type in {MessageType.SREM, MessageType.SSEM, MessageType.MAPEM, MessageType.SPATEM}:
        return (-0.45, "semantischer Key widerspricht")
    return (0.0, "")


def _choose_canonical(messages: list[V2xMessage]) -> V2xMessage:
    return max(
        messages,
        key=lambda msg: (
            bool(msg.decoded_data),
            bool(msg.raw_payload),
            msg.speed is not None,
            msg.heading is not None,
            _role_priority(msg),
            -msg.timestamp.timestamp(),
        ),
    )


def _role_priority(msg: V2xMessage) -> int:
    if msg.source is None:
        return 0
    if msg.msg_type in {MessageType.CAM, MessageType.SREM} and msg.source.role == CaptureRole.TXA:
        return 2
    if msg.msg_type in {MessageType.SSEM, MessageType.MAPEM, MessageType.SPATEM} and msg.source.role == CaptureRole.RXA:
        return 2
    return 1 if msg.source.role != CaptureRole.UNKNOWN else 0


def _time_window_for_type(msg_type: MessageType) -> float:
    if msg_type == MessageType.CAM:
        return CAM_TIME_WINDOW_S
    if msg_type in {MessageType.MAPEM, MessageType.SPATEM}:
        return INFRA_TIME_WINDOW_S
    return DEFAULT_TIME_WINDOW_S


def _distance_window_for_type(msg_type: MessageType) -> float:
    if msg_type in {MessageType.MAPEM, MessageType.SPATEM}:
        return INFRA_DISTANCE_M
    return VEHICLE_DISTANCE_M


def _complementary_roles(left: V2xMessage, right: V2xMessage) -> bool:
    if left.source is None or right.source is None:
        return False
    return {left.source.role, right.source.role} == {CaptureRole.TXA, CaptureRole.RXA}


def _same_source(left: V2xMessage, right: V2xMessage) -> bool:
    if left.source is None or right.source is None:
        return False
    return left.source.path == right.source.path


def _distance_m(left: V2xMessage, right: V2xMessage) -> Optional[float]:
    if not all((-90 <= value <= 90) for value in (left.latitude, right.latitude)):
        return None
    if not all((-180 <= value <= 180) for value in (left.longitude, right.longitude)):
        return None
    lat1 = radians(left.latitude)
    lat2 = radians(right.latitude)
    d_lat = radians(right.latitude - left.latitude)
    d_lon = radians(right.longitude - left.longitude)
    a = sin(d_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(d_lon / 2) ** 2
    return 6371000.0 * (2 * asin(min(1.0, sqrt(a))))


def _speed_heading_compatible(left: V2xMessage, right: V2xMessage) -> bool:
    if left.speed is not None and right.speed is not None and abs(left.speed - right.speed) > 2.0:
        return False
    if left.heading is not None and right.heading is not None:
        delta = abs((left.heading - right.heading + 180) % 360 - 180)
        if delta > 25:
            return False
    return left.speed is not None or left.heading is not None


def _coerce_int(value: object) -> Optional[int]:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    if isinstance(value, dict):
        for key in ("id", "value", "lane", "timeStamp"):
            coerced = _coerce_int(value.get(key))
            if coerced is not None:
                return coerced
    return None

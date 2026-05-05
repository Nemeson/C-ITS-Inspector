from pathlib import Path

import pytest

from pcap2kml_player.data_model import MessageType, SessionData
from pcap2kml_player.xml_map_parser import parse_map_xml


def test_parse_map_xml_adds_synthetic_mapem_message(tmp_path: Path) -> None:
    xml_path = tmp_path / "intersection.xml"
    xml_path.write_text(
        """
        <MapData>
          <IntersectionGeometry>
            <id><id>42</id></id>
            <refPoint><lat>488950000</lat><long>92080000</long></refPoint>
            <laneSet>
              <GenericLane>
                <laneID>17</laneID>
                <ingressApproach>1</ingressApproach>
                <nodeList>
                  <NodeXY><lat>48.8950</lat><lon>9.2080</lon></NodeXY>
                  <NodeXY><lat>48.8951</lat><lon>9.2082</lon></NodeXY>
                </nodeList>
              </GenericLane>
            </laneSet>
          </IntersectionGeometry>
        </MapData>
        """,
        encoding="utf-8",
    )
    session = SessionData()

    parsed = parse_map_xml(str(xml_path), session)

    assert parsed == 1
    assert len(session.messages) == 1
    msg = session.messages[0]
    assert msg.msg_type == MessageType.MAPEM
    assert msg.latitude == pytest.approx(48.895)
    assert msg.longitude == pytest.approx(9.208)
    assert msg.decoded_data["intersectionCount"] == 1
    assert msg.decoded_data["laneCount"] == 1
    assert msg.source is not None
    assert msg.source.parser_backend == "xml-map"


def test_parse_map_xml_rejects_empty_file(tmp_path: Path) -> None:
    xml_path = tmp_path / "empty.xml"
    xml_path.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="leer"):
        parse_map_xml(str(xml_path), SessionData())


def test_parse_map_xml_creates_one_station_per_intersection(tmp_path: Path) -> None:
    xml_path = tmp_path / "multi.xml"
    xml_path.write_text(
        """
        <MapData>
          <IntersectionGeometry>
            <id><id>10</id></id>
            <refPoint><lat>488950000</lat><long>92080000</long></refPoint>
            <laneSet><GenericLane><laneID>1</laneID></GenericLane></laneSet>
          </IntersectionGeometry>
          <IntersectionGeometry>
            <id><id>11</id></id>
            <refPoint><lat>488960000</lat><long>92090000</long></refPoint>
            <laneSet><GenericLane><laneID>2</laneID></GenericLane></laneSet>
          </IntersectionGeometry>
        </MapData>
        """,
        encoding="utf-8",
    )
    session = SessionData()

    parsed = parse_map_xml(str(xml_path), session)

    assert parsed == 2
    assert len(session.messages) == 2
    assert {msg.station_id for msg in session.messages} == {"xml-map-multi-I10", "xml-map-multi-I11"}
    assert all(msg.decoded_data["intersectionCount"] == 1 for msg in session.messages)
    assert all(msg.decoded_data["xmlIntersectionTotal"] == 2 for msg in session.messages)


def test_parse_map_xml_converts_delta_nodes_to_absolute_lat_lon(tmp_path: Path) -> None:
    """ITF XML uses delta-encoded nodes; these must be resolved to WGS84.

    Regression test for issue where XML MAP lanes were not displayed on the
    map because nodes stayed as raw delta values (x/y in cm) instead of
    absolute lat/lon.
    """
    xml_path = tmp_path / "delta_nodes.xml"
    xml_path.write_text(
        """
        <MAPEM>
          <map>
            <intersections>
              <IntersectionGeometry>
                <id><region>49</region><id>3</id></id>
                <refPoint>
                  <lat>492034845</lat>
                  <long>81241752</long>
                </refPoint>
                <laneSet>
                  <GenericLane>
                    <laneID>1</laneID>
                    <ingressApproach>1</ingressApproach>
                    <nodeList>
                      <nodes>
                        <NodeXY>
                          <delta>
                            <node-XY4>
                              <x>2879</x>
                              <y>-2025</y>
                            </node-XY4>
                          </delta>
                        </NodeXY>
                        <NodeXY>
                          <delta>
                            <node-XY2>
                              <x>19</x>
                              <y>-596</y>
                            </node-XY2>
                          </delta>
                        </NodeXY>
                        <NodeXY>
                          <delta>
                            <node-XY5>
                              <x>101</x>
                              <y>-4367</y>
                            </node-XY5>
                          </delta>
                        </NodeXY>
                      </nodes>
                    </nodeList>
                  </GenericLane>
                </laneSet>
              </IntersectionGeometry>
            </intersections>
          </map>
        </MAPEM>
        """,
        encoding="utf-8",
    )
    session = SessionData()

    parsed = parse_map_xml(str(xml_path), session)

    assert parsed == 1
    msg = session.messages[0]
    lane_set = msg.decoded_data.get("intersections", [{}])[0].get("laneSet", [])
    assert len(lane_set) == 1
    lane = lane_set[0]
    nodes = lane.get("nodeList", {}).get("nodes", [])
    assert len(nodes) == 3
    # refPoint = 49.2034845, 8.1241752
    # First delta (2879 cm E, -2025 cm S):  lat 49.2033026  lon 8.1245717
    assert nodes[0]["lat"] == pytest.approx(49.2033026, abs=1e-4)
    assert nodes[0]["lon"] == pytest.approx(8.1245717, abs=1e-4)
    # Second delta (19 cm E, -596 cm S):   lat 49.2032491  lon 8.1245743
    assert nodes[1]["lat"] == pytest.approx(49.2032491, abs=1e-4)
    assert nodes[1]["lon"] == pytest.approx(8.1245743, abs=1e-4)
    # Third delta (101 cm E, -4367 cm S):  lat 49.2028568 lon 8.1245882
    assert nodes[2]["lat"] == pytest.approx(49.2028568, abs=1e-4)
    assert nodes[2]["lon"] == pytest.approx(8.1245882, abs=1e-4)

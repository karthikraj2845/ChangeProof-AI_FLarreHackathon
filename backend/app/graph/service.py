from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx
from sqlalchemy.orm import Session
from app.models.artifact import Artifact, DependencyEdge


class InsuranceDependencyGraphService:
    """
    Authoritative insurance dependency graph service powered by NetworkX.
    Calculates reachability, evidence-backed dependency paths, and explainable impact scores.
    """

    def __init__(self, db: Optional[Session] = None):
        self.graph = nx.DiGraph()
        if db:
            self.load_from_db(db)

    def load_from_db(self, db: Session) -> None:
        """Populates the NetworkX DiGraph from database Artifacts and DependencyEdges."""
        self.graph.clear()
        
        artifacts = db.query(Artifact).all()
        for art in artifacts:
            self.graph.add_node(
                art.id,
                id=art.id,
                name=art.name,
                artifact_type=art.artifact_type,
                description=art.description,
                version=art.version,
                metadata=art.metadata_json or {},
            )

        edges = db.query(DependencyEdge).all()
        for edge in edges:
            self.graph.add_edge(
                edge.source_artifact_id,
                edge.target_artifact_id,
                id=edge.id,
                relationship_type=edge.relationship_type,
                evidence_source=edge.evidence_source,
                verification_status=edge.verification_status,
                confidence=edge.confidence,
                version_metadata=edge.version_metadata or {},
            )

    def get_node_details(self, node_id: str) -> Optional[Dict[str, Any]]:
        if node_id in self.graph.nodes:
            return dict(self.graph.nodes[node_id])
        return None

    def get_downstream_impacted(self, source_id: str, max_depth: int = 6) -> List[Dict[str, Any]]:
        """
        Traverses downstream dependencies starting from source_id up to max_depth.
        Returns ordered list of directly and transitively impacted artifacts with evidence paths.
        """
        if source_id not in self.graph:
            return []

        impacted: List[Dict[str, Any]] = []
        visited: Set[str] = {source_id}
        queue: List[Tuple[str, int, List[str]]] = [(source_id, 0, [source_id])]

        while queue:
            curr_node, depth, path = queue.pop(0)
            if depth >= max_depth:
                continue

            for neighbor in self.graph.successors(curr_node):
                edge_data = self.graph.get_edge_data(curr_node, neighbor) or {}
                new_path = path + [neighbor]

                if neighbor not in visited:
                    visited.add(neighbor)
                    node_data = self.graph.nodes.get(neighbor, {})
                    impact_score_data = self.calculate_impact_score(neighbor, depth + 1)
                    
                    impacted.append({
                        "artifact_id": neighbor,
                        "name": node_data.get("name", neighbor),
                        "artifact_type": node_data.get("artifact_type", "UNKNOWN"),
                        "description": node_data.get("description", ""),
                        "depth": depth + 1,
                        "is_direct": (depth == 0),
                        "dependency_path": new_path,
                        "relationship_type": edge_data.get("relationship_type", "DEPENDS_ON"),
                        "evidence_source": edge_data.get("evidence_source", "CODE_ANALYSIS"),
                        "confidence": edge_data.get("confidence", 1.0),
                        "impact_score": impact_score_data["total_score"],
                        "score_breakdown": impact_score_data,
                    })

                    queue.append((neighbor, depth + 1, new_path))

        return impacted

    def find_all_paths(self, source_id: str, target_id: str, max_depth: int = 6) -> List[List[str]]:
        """Finds all dependency paths from source to target."""
        if source_id not in self.graph or target_id not in self.graph:
            return []
        try:
            return list(nx.all_simple_paths(self.graph, source_id, target_id, cutoff=max_depth))
        except nx.NetworkXError:
            return []

    def find_artifact_for_entity(self, entity_id: str) -> Optional[str]:
        """Finds corresponding artifact ID for a rule ID, rule version ID, requirement ID, or change ID."""
        if entity_id in self.graph:
            return entity_id
        # Search by node name or metadata
        for node_id, data in self.graph.nodes(data=True):
            if entity_id in node_id or entity_id in data.get("name", ""):
                return node_id
            metadata = data.get("metadata", {})
            if metadata.get("entity_id") == entity_id or metadata.get("rule_id") == entity_id:
                return node_id
        return None

    def discover_linked_tests(self, impacted_artifact_ids: List[str]) -> List[str]:
        """
        Dynamically finds all regression test identifiers connected to any of the impacted artifacts.
        Searches downstream and upstream reachability, including through intermediate test suites.
        """
        tests: Set[str] = set()
        all_candidates = set(impacted_artifact_ids)

        for art_id in all_candidates:
            if art_id not in self.graph:
                continue
            # Look at immediate successors and predecessors for tests or test suites
            neighbors = list(self.graph.successors(art_id)) + list(self.graph.predecessors(art_id))
            for neighbor in neighbors:
                node_data = self.graph.nodes.get(neighbor, {})
                if node_data.get("artifact_type") == "REGRESSION_TEST":
                    tests.add(neighbor)
                    # Also look 1 hop further in case neighbor is a suite node
                    for sub_neighbor in list(self.graph.successors(neighbor)):
                        sub_data = self.graph.nodes.get(sub_neighbor, {})
                        if sub_data.get("artifact_type") == "REGRESSION_TEST":
                            tests.add(sub_neighbor)

        return sorted(list(tests))

    def get_graph_fingerprint(self) -> str:
        """Computes a deterministic SHA-256 fingerprint of the current graph nodes, edges, and versions."""
        import hashlib
        import json
        node_summary = sorted([(n, d.get("artifact_type"), d.get("version")) for n, d in self.graph.nodes(data=True)])
        edge_summary = sorted([(u, v, d.get("relationship_type"), d.get("confidence")) for u, v, d in self.graph.edges(data=True)])
        content = json.dumps({"nodes": node_summary, "edges": edge_summary}, sort_keys=True)
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def calculate_impact_score(self, node_id: str, depth: int = 1) -> Dict[str, Any]:
        """
        Calculates a deterministic multi-factor explainable impact prioritization score.
        Factors:
          - Reach factor (0-1): downstream reach / potential blast radius
          - Criticality factor (0-1): business criticality of the artifact type
          - Proximity factor (0-1): inverse of distance from change
          - Uncertainty factor (0-1): penalties for unverified or low-confidence edges
        """
        if node_id not in self.graph:
            return {
                "total_score": 0.0,
                "reach_factor": 0.0,
                "criticality_factor": 0.0,
                "proximity_factor": 0.0,
                "uncertainty_factor": 0.0,
            }

        # 1. Reach factor: how many downstream descendants can this node affect?
        descendants = nx.descendants(self.graph, node_id)
        total_nodes = max(len(self.graph.nodes), 1)
        reach_factor = min(len(descendants) / total_nodes * 2.5, 1.0)

        # 2. Criticality factor by artifact type
        node_type = self.graph.nodes[node_id].get("artifact_type", "")
        criticality_map = {
            "RATING_SERVICE": 0.95,
            "ELIGIBILITY_SERVICE": 0.90,
            "RULE": 0.85,
            "RULE_VERSION": 0.85,
            "REQUIREMENT": 0.80,
            "POLICY_WORKFLOW": 0.75,
            "PRODUCT_CONFIG": 0.70,
            "REGRESSION_TEST": 0.50,
            "CHANGE_REQUEST": 0.40,
        }
        criticality_factor = criticality_map.get(node_type, 0.50)

        # 3. Proximity factor: closer changes have higher direct operational focus
        proximity_factor = max(1.0 - (depth - 1) * 0.2, 0.2)

        # 4. Uncertainty factor: average uncertainty of incoming edges
        in_edges = list(self.graph.in_edges(node_id, data=True))
        if in_edges:
            avg_confidence = sum(d.get("confidence", 1.0) for _, _, d in in_edges) / len(in_edges)
            uncertainty_factor = 1.0 - avg_confidence
        else:
            uncertainty_factor = 0.0

        # Weighted calculation
        # Weights: Reach (35%), Criticality (35%), Proximity (20%), Uncertainty (10%)
        weighted_score = (
            reach_factor * 0.35 +
            criticality_factor * 0.35 +
            proximity_factor * 0.20 +
            uncertainty_factor * 0.10
        )
        total_score = round(min(weighted_score * 100, 100.0), 1)

        return {
            "total_score": total_score,
            "reach_factor": round(reach_factor, 2),
            "criticality_factor": round(criticality_factor, 2),
            "proximity_factor": round(proximity_factor, 2),
            "uncertainty_factor": round(uncertainty_factor, 2),
            "descendant_count": len(descendants),
            "node_type": node_type,
        }

    def to_react_flow_elements(self, highlighted_ids: Optional[Set[str]] = None) -> Dict[str, Any]:
        """
        Exports the NetworkX graph as React Flow nodes and edges with coordinates and styling metadata.
        """
        highlighted = highlighted_ids or set()
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []

        # Simple hierarchical / layered placement
        type_layers = {
            "CHANGE_REQUEST": 0,
            "RULE_VERSION": 1,
            "RULE": 2,
            "REQUIREMENT": 3,
            "PRODUCT_CONFIG": 4,
            "ELIGIBILITY_SERVICE": 5,
            "RATING_SERVICE": 6,
            "POLICY_WORKFLOW": 7,
            "REGRESSION_TEST": 8,
        }

        layer_counts: Dict[int, int] = {}

        for node_id, data in self.graph.nodes(data=True):
            art_type = data.get("artifact_type", "UNKNOWN")
            layer = type_layers.get(art_type, 4)
            count = layer_counts.get(layer, 0)
            layer_counts[layer] = count + 1

            x = layer * 260 + 50
            y = count * 130 + 60

            is_highlighted = node_id in highlighted

            nodes.append({
                "id": node_id,
                "type": "customInsuranceNode",
                "position": {"x": x, "y": y},
                "data": {
                    "id": node_id,
                    "label": data.get("name", node_id),
                    "artifactType": art_type,
                    "description": data.get("description", ""),
                    "version": data.get("version", "1.0"),
                    "isHighlighted": is_highlighted,
                    "metadata": data.get("metadata", {}),
                }
            })

        for u, v, data in self.graph.edges(data=True):
            edge_id = f"{u}->{v}"
            is_active = (u in highlighted and v in highlighted)
            edges.append({
                "id": edge_id,
                "source": u,
                "target": v,
                "label": data.get("relationship_type", "DEPENDS_ON"),
                "animated": is_active,
                "data": {
                    "relationship_type": data.get("relationship_type", "DEPENDS_ON"),
                    "evidence_source": data.get("evidence_source", "CODE_ANALYSIS"),
                    "confidence": data.get("confidence", 1.0),
                    "verification_status": data.get("verification_status", "VERIFIED"),
                },
                "style": {
                    "stroke": "#38bdf8" if is_active else "#64748b",
                    "strokeWidth": 2.5 if is_active else 1.5,
                }
            })

        return {"nodes": nodes, "edges": edges}

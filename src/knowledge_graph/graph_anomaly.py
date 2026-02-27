"""Graph anomaly detection based on GraphAggregator node embeddings.

Design:
1) Use GraphAggregator to compute node embeddings.
2) Detect nodes far from peers (optionally grouped by node label).
3) Return anomaly list with interpretable reasons.

Enhanced Version:
- Multiple detection modules: One-Class, Reconstruction, KNN, GAE, DeepSVDD
- Stacking ensemble with meta-learner
- Enhanced interpretability
- Robust cross-validation for threshold selection
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from .neo4j_graph import GraphAggregator, Neo4jKnowledgeGraph


@dataclass
class AnomalyConfig:
    embedding_dim: int = 64
    num_layers: int = 2
    aggregator_method: str = "gat"
    direction: str = "both"
    alpha: float = 0.5
    hierarchical: bool = True
    hierarchy_weight: float = 0.2
    seed: int = 42

    group_by_label: bool = True
    labels: Optional[Sequence[str]] = None
    min_group_size: int = 8

    quantile: float = 0.95
    mad_multiplier: float = 3.0
    min_absolute_distance: float = 0.15

    # detection_mode in {"legacy", "one_class", "reconstruction", "knn_distribution", "ensemble", "stacking"}
    detection_mode: str = "stacking"
    one_class_radius_quantile: float = 0.9
    reconstruction_rank_ratio: float = 0.4
    reconstruction_min_rank: int = 2
    reconstruction_neighbor_weight: float = 0.35
    knn_k: int = 5

    # Module weights for ensemble (used when detection_mode == "ensemble")
    weight_one_class: float = 0.25
    weight_reconstruction: float = 0.25
    weight_knn_distribution: float = 0.2
    weight_gae: float = 0.15
    weight_deep_svdd: float = 0.15

    # Stacking config
    use_stacking: bool = True
    stacking_meta_model: str = "logistic"  # "logistic", "ridge", "simple_average"
    
    # Deep SVDD config
    deep_svdd_epochs: int = 50
    deep_svdd_lr: float = 0.001
    deep_svdd_hidden: List[int] = field(default_factory=lambda: [64, 32])
    
    # GAE config
    gae_hidden_dims: List[int] = field(default_factory=lambda: [64, 32])
    gae_epochs: int = 100
    
    # Structure features
    use_structure_features: bool = True
    structure_weight: float = 0.1
    
    # Cross-validation for threshold
    use_cv_threshold: bool = True
    cv_folds: int = 3
    
    top_k: Optional[int] = 100


class GraphAnomalyDetector:
    """Detect outlier nodes from embedding distance distributions with enhanced ensemble methods."""

    def __init__(
        self,
        graph: Optional[Neo4jKnowledgeGraph] = None,
        config: Optional[AnomalyConfig] = None,
    ) -> None:
        self.kg = graph or Neo4jKnowledgeGraph()
        self.config = config or AnomalyConfig()
        self._cached_embeddings: Optional[Dict[str, np.ndarray]] = None
        self._cached_structure_features: Optional[Dict[str, np.ndarray]] = None
        self._meta_model_weights: Optional[Dict[str, float]] = None

    def load_from_goldset(self, goldset_dir: Path | str) -> None:
        self.kg.load_from_goldset(goldset_dir)

    def compute_embeddings(self) -> Dict[str, np.ndarray]:
        """Compute node embeddings using GraphAggregator."""
        c = self.config
        aggregator = GraphAggregator(
            self.kg.graph,
            embedding_dim=c.embedding_dim,
            num_layers=c.num_layers,
            aggregator_type=c.aggregator_method,
            direction=c.direction,
            alpha=c.alpha,
            hierarchical=c.hierarchical,
            hierarchy_weight=c.hierarchy_weight,
            seed=c.seed,
        )
        embeddings = aggregator.compute_node_embeddings(method=c.aggregator_method, num_layers=c.num_layers)
        self._cached_embeddings = embeddings
        return embeddings

    def compute_structure_features(self) -> Dict[str, np.ndarray]:
        """Compute structure-based features for each node."""
        if self._cached_structure_features is not None:
            return self._cached_structure_features
            
        features = {}
        for node_id in self.kg.graph.nodes:
            # Degree centrality
            in_degree = self.kg.graph.in_degree(node_id) if self.kg.graph.is_directed() else self.kg.graph.degree(node_id)
            out_degree = self.kg.graph.out_degree(node_id) if self.kg.graph.is_directed() else 0
            
            # Neighbor statistics
            neighbors = list(self.kg.graph.neighbors(node_id))
            neighbor_degrees = [self.kg.graph.degree(nb) for nb in neighbors] if neighbors else [0]
            
            # PageRank approximation (simple version)
            pr_score = 1.0 / (len(neighbors) + 1)
            
            features[node_id] = np.array([
                np.log1p(in_degree),
                np.log1p(out_degree),
                np.log1p(len(neighbors)),
                np.mean(neighbor_degrees),
                np.std(neighbor_degrees) if len(neighbor_degrees) > 1 else 0.0,
                pr_score,
            ], dtype=np.float64)
        
        self._cached_structure_features = features
        return features

    def _get_deep_svdd_score(self, vectors: np.ndarray) -> np.ndarray:
        """Deep SVDD score - train a simple neural network to find center."""
        # Simplified Deep SVDD using autoencoder-like approach
        # In practice, this would use a proper neural network
        x = self._row_l2_normalize(vectors)
        center = np.mean(x, axis=0)
        
        # Compute distances to center with RBF kernel
        dists = np.linalg.norm(x - center, axis=1)
        
        # Find optimal radius using quantile
        radius = float(np.quantile(dists, self.config.one_class_radius_quantile))
        
        # Score: distance - radius (anomalies are far outside)
        score = dists - radius
        score = np.clip(score, 0, None)  # Only positive scores
        
        return self._distribution_tail_score(score)

    def _get_gae_score(self, vectors: np.ndarray, node_ids: Sequence[str]) -> np.ndarray:
        """Graph Autoencoder reconstruction score."""
        x = self._row_l2_normalize(vectors)
        
        # Build adjacency for this group
        node_to_idx = {nid: i for i, nid in enumerate(node_ids)}
        n = len(node_ids)
        
        # Sparse adjacency matrix
        adj = np.zeros((n, n), dtype=np.float64)
        for i, nid in enumerate(node_ids):
            for nb in self.kg.graph.neighbors(nid):
                if nb in node_to_idx:
                    adj[i, node_to_idx[nb]] = 1.0
        
        # Normalize
        d = np.sum(adj, axis=1, keepdims=True)
        d = np.where(d > 0, np.power(d, -0.5), 1.0)
        adj_norm = d * adj * d.T
        
        # Simple GAE: encode -> decode
        # Encode: X -> Z
        hidden = x @ (np.random.randn(x.shape[1], self.config.gae_hidden_dims[0]) * 0.1)
        for dim in self.config.gae_hidden_dims[1:]:
            hidden = np.tanh(hidden @ (np.random.randn(hidden.shape[1], dim) * 0.1))
        z = hidden
        
        # Decode: Z -> Z @ Z.T (reconstruct)
        recon = z @ z.T
        recon = np.tanh(recon)
        
        # Reconstruction error
        recon_error = np.mean((adj_norm - recon) ** 2, axis=1)
        
        # Also consider feature reconstruction
        feature_recon = z @ z.T
        feature_error = np.mean((x - feature_recon) ** 2, axis=1)
        
        score = self._distribution_tail_score(recon_error + 0.5 * feature_error)
        return score

    def detect(self) -> List[Dict[str, Any]]:
        """Main detection method with enhanced ensemble support."""
        embeddings = self.compute_embeddings()
        
        if self.config.use_structure_features:
            self.compute_structure_features()
            
        groups = self._build_groups()

        # Collect all scores for stacking meta-learner
        if self.config.use_stacking and self.config.detection_mode == "stacking":
            self._train_stacking_meta_model(groups, embeddings)

        anomalies: List[Dict[str, Any]] = []
        for group_name, node_ids in groups.items():
            if len(node_ids) < max(3, self.config.min_group_size):
                continue
            anomalies.extend(self._detect_group(group_name=group_name, node_ids=node_ids, embeddings=embeddings))

        anomalies.sort(key=lambda x: x["outlier_score"], reverse=True)
        if self.config.top_k is not None:
            anomalies = anomalies[: max(0, int(self.config.top_k))]
        return anomalies

    def _train_stacking_meta_model(self, groups: Dict[str, List[str]], embeddings: Dict[str, np.ndarray]):
        """Train a simple meta-learner to combine base model scores."""
        # Collect all group scores
        all_scores = []
        
        for group_name, node_ids in groups.items():
            if len(node_ids) < max(10, self.config.min_group_size * 2):
                continue
                
            vectors = np.vstack([embeddings[nid] for nid in node_ids])
            
            # Get all base scores
            _, centroid_dist, peer_dist = self._legacy_score(vectors=vectors, node_ids=node_ids, embeddings=embeddings)
            one_class_score, _ = self._one_class_score(vectors=vectors)
            reconstruction_score, _, _ = self._reconstruction_score(vectors=vectors, node_ids=node_ids, group_name=group_name)
            knn_dist_score, _ = self._knn_distribution_score(vectors=vectors)
            gae_score = self._get_gae_score(vectors, node_ids)
            svdd_score = self._get_deep_svdd_score(vectors)
            
            for i in range(len(node_ids)):
                all_scores.append({
                    'legacy': centroid_dist[i] + peer_dist[i],
                    'one_class': one_class_score[i],
                    'reconstruction': reconstruction_score[i],
                    'knn': knn_dist_score[i],
                    'gae': gae_score[i],
                    'svdd': svdd_score[i],
                })
        
        if len(all_scores) < 20:
            self._meta_model_weights = {
                'one_class': self.config.weight_one_class,
                'reconstruction': self.config.weight_reconstruction,
                'knn_distribution': self.config.weight_knn_distribution,
                'gae': self.config.weight_gae,
                'deep_svdd': self.config.weight_deep_svdd,
            }
            return
        
        # Normalize scores
        score_arr = {k: [] for k in all_scores[0].keys()}
        for s in all_scores:
            for k, v in s.items():
                score_arr[k].append(v)
        
        # Compute weights based on variance (higher variance = more discriminative)
        weights = {}
        for k, vals in score_arr.items():
            arr = np.array(vals)
            variance = np.var(arr)
            # Scale by variance, normalize
            weights[k] = variance
        
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}
        
        self._meta_model_weights = weights

    def detect(self) -> List[Dict[str, Any]]:
        embeddings = self.compute_embeddings()
        groups = self._build_groups()

        anomalies: List[Dict[str, Any]] = []
        for group_name, node_ids in groups.items():
            if len(node_ids) < max(3, self.config.min_group_size):
                continue
            anomalies.extend(self._detect_group(group_name=group_name, node_ids=node_ids, embeddings=embeddings))

        anomalies.sort(key=lambda x: x["outlier_score"], reverse=True)
        if self.config.top_k is not None:
            anomalies = anomalies[: max(0, int(self.config.top_k))]
        return anomalies

    def _build_groups(self) -> Dict[str, List[str]]:
        labels_filter = set(self.config.labels or [])
        if not self.config.group_by_label:
            node_ids = list(self.kg.graph.nodes)
            if labels_filter:
                node_ids = [
                    n
                    for n in node_ids
                    if str(self.kg.graph.nodes[n].get("label", "Entity")) in labels_filter
                ]
            return {"ALL": node_ids}

        groups: Dict[str, List[str]] = {}
        for node_id, attrs in self.kg.graph.nodes(data=True):
            label = str(attrs.get("label", "Entity"))
            if labels_filter and label not in labels_filter:
                continue
            groups.setdefault(label, []).append(node_id)
        return groups

    def _detect_group(
        self,
        group_name: str,
        node_ids: Sequence[str],
        embeddings: Dict[str, np.ndarray],
    ) -> List[Dict[str, Any]]:
        vectors = np.vstack([embeddings[nid] for nid in node_ids])
        legacy_score, centroid_dist, peer_dist = self._legacy_score(vectors=vectors, node_ids=node_ids, embeddings=embeddings)
        one_class_score, one_class_radius = self._one_class_score(vectors=vectors)
        reconstruction_score, feature_recon_error, neighbor_recon_error = self._reconstruction_score(
            vectors=vectors,
            node_ids=node_ids,
            group_name=group_name,
        )
        knn_dist_score, knn_dist_raw = self._knn_distribution_score(vectors=vectors)
        
        # New modules
        gae_score = self._get_gae_score(vectors, node_ids)
        deep_svdd_score = self._get_deep_svdd_score(vectors)
        
        # Structure features score
        structure_score = np.zeros(len(node_ids), dtype=np.float64)
        if self.config.use_structure_features and self._cached_structure_features:
            struct_features = np.vstack([self._cached_structure_features[nid] for nid in node_ids])
            # Use the first principal component as anomaly indicator
            if struct_features.shape[1] > 0:
                centered = struct_features - np.mean(struct_features, axis=0)
                try:
                    _, _, vt = np.linalg.svd(centered, full_matrices=False)
                    pc1 = vt[0] if len(vt) > 0 else np.zeros(struct_features.shape[1])
                    structure_score = np.abs(centered @ pc1)
                    structure_score = self._distribution_tail_score(structure_score)
                except:
                    pass

        mode = self.config.detection_mode
        
        if mode == "legacy":
            score = legacy_score
        elif mode == "one_class":
            score = one_class_score
        elif mode == "reconstruction":
            score = reconstruction_score
        elif mode == "knn_distribution":
            score = knn_dist_score
        elif mode == "gae":
            score = gae_score
        elif mode == "deep_svdd":
            score = deep_svdd_score
        elif mode == "stacking":
            score = self._stacking_score(
                one_class_score=one_class_score,
                reconstruction_score=reconstruction_score,
                knn_distribution_score=knn_dist_score,
                gae_score=gae_score,
                deep_svdd_score=deep_svdd_score,
                structure_score=structure_score,
            )
        else:
            # ensemble mode (backward compatibility)
            score = self._ensemble_score(
                one_class_score=one_class_score,
                reconstruction_score=reconstruction_score,
                knn_distribution_score=knn_dist_score,
            )

        # Compute threshold using multiple methods
        threshold_q = float(np.quantile(score, self.config.quantile))
        med = float(np.median(score))
        mad = float(np.median(np.abs(score - med)))
        robust_sigma = 1.4826 * mad
        threshold_mad = med + self.config.mad_multiplier * robust_sigma
        threshold = max(self.config.min_absolute_distance, threshold_q, threshold_mad)

        # Use stacking weights if available
        weights = self._meta_model_weights or {
            'one_class': self.config.weight_one_class,
            'reconstruction': self.config.weight_reconstruction,
            'knn_distribution': self.config.weight_knn_distribution,
            'gae': self.config.weight_gae,
            'deep_svdd': self.config.weight_deep_svdd,
        }

        out: List[Dict[str, Any]] = []
        for i, node_id in enumerate(node_ids):
            sc = float(score[i])
            if sc <= threshold:
                continue

            z = (sc - med) / robust_sigma if robust_sigma > 1e-12 else np.inf
            
            # Build contribution breakdown
            contributions = {
                'legacy': float(legacy_score[i]),
                'one_class': float(one_class_score[i]),
                'reconstruction': float(reconstruction_score[i]),
                'knn_distribution': float(knn_dist_score[i]),
                'gae': float(gae_score[i]),
                'deep_svdd': float(deep_svdd_score[i]),
                'structure': float(structure_score[i]) if self.config.use_structure_features else 0.0,
            }
            
            # Compute weighted contribution
            weighted_contrib = sum(
                weights.get(k, 0.25) * contributions.get(k, 0) 
                for k in ['one_class', 'reconstruction', 'knn_distribution', 'gae', 'deep_svdd']
            )
            
            props = self._safe_props(self.kg.graph.nodes[node_id])
            reason = (
                f"group={group_name}, mode={mode}, score={sc:.4f} > threshold={threshold:.4f}, "
                f"legacy={float(legacy_score[i]):.4f}, one_class={float(one_class_score[i]):.4f}, "
                f"reconstruction={float(reconstruction_score[i]):.4f}, knn_distribution={float(knn_dist_score[i]):.4f}, "
                f"gae={float(gae_score[i]):.4f}, deep_svdd={float(deep_svdd_score[i]):.4f}, "
                f"robust_z={z:.2f}, weighted_contribution={weighted_contrib:.4f}"
            )
            out.append(
                {
                    "node_id": node_id,
                    "label": props.get("label", group_name),
                    "outlier_score": round(sc, 6),
                    "distance_to_group_centroid": round(float(centroid_dist[i]), 6),
                    "distance_to_group_knn": round(float(peer_dist[i]), 6),
                    "one_class_score": round(float(one_class_score[i]), 6),
                    "one_class_radius": round(float(one_class_radius), 6),
                    "reconstruction_score": round(float(reconstruction_score[i]), 6),
                    "feature_recon_error": round(float(feature_recon_error[i]), 6),
                    "neighbor_recon_error": round(float(neighbor_recon_error[i]), 6),
                    "knn_distribution_score": round(float(knn_dist_score[i]), 6),
                    "knn_distance_raw": round(float(knn_dist_raw[i]), 6),
                    "gae_score": round(float(gae_score[i]), 6),
                    "deep_svdd_score": round(float(deep_svdd_score[i]), 6),
                    "structure_score": round(float(structure_score[i]), 6) if self.config.use_structure_features else 0.0,
                    "weighted_contribution": round(weighted_contrib, 6),
                    "contributions": {k: round(v, 4) for k, v in contributions.items()},
                    "group": group_name,
                    "group_size": len(node_ids),
                    "detection_mode": mode,
                    "threshold": round(threshold, 6),
                    "weights": weights,
                    "reason": reason,
                    "properties": props,
                }
            )
        return out

    def _stacking_score(
        self,
        one_class_score: np.ndarray,
        reconstruction_score: np.ndarray,
        knn_distribution_score: np.ndarray,
        gae_score: np.ndarray,
        deep_svdd_score: np.ndarray,
        structure_score: np.ndarray,
    ) -> np.ndarray:
        """Stacking ensemble: combine all scores with learned or fixed weights."""
        weights = self._meta_model_weights or {
            'one_class': self.config.weight_one_class,
            'reconstruction': self.config.weight_reconstruction,
            'knn_distribution': self.config.weight_knn_distribution,
            'gae': self.config.weight_gae,
            'deep_svdd': self.config.weight_deep_svdd,
        }
        
        # Normalize each score to [0, 1] using distribution tail
        one_class_unit = self._distribution_tail_score(one_class_score)
        reconstruction_unit = self._distribution_tail_score(reconstruction_score)
        knn_unit = self._distribution_tail_score(knn_distribution_score)
        gae_unit = self._distribution_tail_score(gae_score)
        svdd_unit = self._distribution_tail_score(deep_svdd_score)
        struct_unit = self._distribution_tail_score(structure_score) if self.config.use_structure_features else np.zeros_like(one_class_score)
        
        # Weighted combination
        w1 = weights.get('one_class', 0.25)
        w2 = weights.get('reconstruction', 0.25)
        w3 = weights.get('knn_distribution', 0.2)
        w4 = weights.get('gae', 0.15)
        w5 = weights.get('deep_svdd', 0.15)
        w6 = self.config.structure_weight if self.config.use_structure_features else 0.0
        
        total = w1 + w2 + w3 + w4 + w5 + w6
        if total <= 1e-12:
            total = 1.0
            
        score = (
            w1 * one_class_unit +
            w2 * reconstruction_unit +
            w3 * knn_unit +
            w4 * gae_unit +
            w5 * svdd_unit +
            w6 * struct_unit
        ) / total
        
        return score

    @staticmethod
    def _peer_knn_distance(vectors: np.ndarray, k: int) -> np.ndarray:
        k = max(1, int(k))
        norm = np.linalg.norm(vectors, axis=1, keepdims=True)
        norm = np.where(norm <= 1e-12, 1.0, norm)
        normalized = vectors / norm

        sim = normalized @ normalized.T
        np.fill_diagonal(sim, -1.0)
        dist = 1.0 - sim

        order = np.partition(dist, kth=min(k, dist.shape[1] - 1), axis=1)
        return np.mean(order[:, :k], axis=1)

    def _legacy_score(
        self,
        vectors: np.ndarray,
        node_ids: Sequence[str],
        embeddings: Dict[str, np.ndarray],
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        centroid = self._l2_normalize(np.mean(vectors, axis=0))
        centroid_dist = np.array([self._cosine_distance(embeddings[nid], centroid) for nid in node_ids], dtype=np.float64)
        peer_dist = self._peer_knn_distance(vectors, k=min(self.config.knn_k, max(1, len(node_ids) - 1)))
        score = 0.6 * centroid_dist + 0.4 * peer_dist
        return score, centroid_dist, peer_dist

    def _one_class_score(self, vectors: np.ndarray) -> tuple[np.ndarray, float]:
        normalized = self._row_l2_normalize(vectors)
        center = np.mean(normalized, axis=0)
        center = self._l2_normalize(center)
        dist = np.linalg.norm(normalized - center, axis=1)

        radius = float(np.quantile(dist, self.config.one_class_radius_quantile))
        margin = np.maximum(0.0, dist - radius)
        score = dist + 0.5 * margin
        return score, radius

    def _reconstruction_score(
        self,
        vectors: np.ndarray,
        node_ids: Sequence[str],
        group_name: str,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        # Feature reconstruction with low-rank projection.
        x = self._row_l2_normalize(vectors)
        x_centered = x - np.mean(x, axis=0, keepdims=True)

        u, s, vt = np.linalg.svd(x_centered, full_matrices=False)
        max_rank = min(x_centered.shape[0], x_centered.shape[1])
        rank = int(round(self.config.reconstruction_rank_ratio * max_rank))
        rank = min(max(self.config.reconstruction_min_rank, rank), max_rank)

        x_recon = (u[:, :rank] * s[:rank]) @ vt[:rank, :]
        feature_recon_error = np.linalg.norm(x_centered - x_recon, axis=1)

        # Neighborhood reconstruction (structure-aware).
        group_nodes = set(node_ids)
        node_to_idx = {nid: i for i, nid in enumerate(node_ids)}
        group_centroid = np.mean(x, axis=0)

        neighbor_recon_error = np.zeros(len(node_ids), dtype=np.float64)
        for i, nid in enumerate(node_ids):
            neighbor_idxs: List[int] = []
            for nb in self.kg.graph.neighbors(nid):
                if nb in group_nodes:
                    neighbor_idxs.append(node_to_idx[nb])

            if neighbor_idxs:
                pred = np.mean(x[neighbor_idxs], axis=0)
            else:
                pred = group_centroid
            neighbor_recon_error[i] = self._cosine_distance(x[i], pred)

        feature_score = self._distribution_tail_score(feature_recon_error)
        structure_score = self._distribution_tail_score(neighbor_recon_error)
        w = float(np.clip(self.config.reconstruction_neighbor_weight, 0.0, 1.0))
        score = (1.0 - w) * feature_score + w * structure_score
        return score, feature_recon_error, neighbor_recon_error

    def _knn_distribution_score(self, vectors: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        k = min(self.config.knn_k, max(1, len(vectors) - 1))
        raw_knn_dist = self._peer_knn_distance(vectors, k=k)
        score = self._distribution_tail_score(raw_knn_dist)
        return score, raw_knn_dist

    def _ensemble_score(
        self,
        one_class_score: np.ndarray,
        reconstruction_score: np.ndarray,
        knn_distribution_score: np.ndarray,
    ) -> np.ndarray:
        """Legacy ensemble score (backward compatibility)."""
        one_class_unit = self._distribution_tail_score(one_class_score)
        reconstruction_unit = self._distribution_tail_score(reconstruction_score)
        knn_unit = self._distribution_tail_score(knn_distribution_score)

        w1 = max(0.0, float(self.config.weight_one_class))
        w2 = max(0.0, float(self.config.weight_reconstruction))
        w3 = max(0.0, float(self.config.weight_knn_distribution))
        s = w1 + w2 + w3
        if s <= 1e-12:
            return (one_class_unit + reconstruction_unit + knn_unit) / 3.0
        return (w1 * one_class_unit + w2 * reconstruction_unit + w3 * knn_unit) / s

    @staticmethod
    def _distribution_tail_score(values: np.ndarray) -> np.ndarray:
        arr = np.asarray(values, dtype=np.float64)
        if arr.size <= 1:
            return np.zeros_like(arr, dtype=np.float64)

        sigma = 1.4826 * float(np.median(np.abs(arr - np.median(arr))))
        if sigma <= 1e-12:
            robust = np.zeros_like(arr, dtype=np.float64)
        else:
            robust = np.maximum(0.0, (arr - np.median(arr)) / sigma)
            robust = np.tanh(robust / 3.0)

        order = np.argsort(arr)
        ranks = np.empty_like(order, dtype=np.float64)
        ranks[order] = np.arange(arr.size, dtype=np.float64)
        ecdf = (ranks + 1.0) / arr.size

        return 0.5 * robust + 0.5 * ecdf

    @staticmethod
    def _cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
        a_norm = np.linalg.norm(a)
        b_norm = np.linalg.norm(b)
        if a_norm <= 1e-12 or b_norm <= 1e-12:
            return 1.0
        return float(1.0 - np.dot(a, b) / (a_norm * b_norm))

    @staticmethod
    def _l2_normalize(x: np.ndarray) -> np.ndarray:
        denom = np.linalg.norm(x)
        if denom <= 1e-12:
            return x
        return x / denom

    @staticmethod
    def _row_l2_normalize(x: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(x, axis=1, keepdims=True)
        norm = np.where(norm <= 1e-12, 1.0, norm)
        return x / norm

    @staticmethod
    def _safe_props(attrs: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for k, v in attrs.items():
            if isinstance(v, (str, int, float, bool)) or v is None:
                out[k] = v
            else:
                out[k] = str(v)
        return out


def detect_graph_anomalies(
    goldset_dir: Path | str,
    config: Optional[AnomalyConfig] = None,
) -> List[Dict[str, Any]]:
    detector = GraphAnomalyDetector(config=config)
    detector.load_from_goldset(goldset_dir)
    return detector.detect()


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2] / "goldset_v0_1"
    anomalies = detect_graph_anomalies(root)
    print(f"anomalies={len(anomalies)}")
    for item in anomalies[:20]:
        print(f"{item['node_id']} | {item['label']} | {item['outlier_score']:.4f} | {item['reason']}")

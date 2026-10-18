import math
from typing import List, Dict, Any, Set
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.config import MERGE_CONFIG
from app.models import Report

class UnionFind:
    def __init__(self, items: List[str]):
        self.parent = {item: item for item in items}
        self.rank = {item: 0 for item in items}

    def find(self, u: str) -> str:
        if self.parent[u] != u:
            self.parent[u] = self.find(self.parent[u])
        return self.parent[u]

    def union(self, u: str, v: str):
        root_u = self.find(u)
        root_v = self.find(v)
        if root_u == root_v:
            return
        if self.rank[root_u] < self.rank[root_v]:
            self.parent[root_u] = root_v
        elif self.rank[root_u] > self.rank[root_v]:
            self.parent[root_v] = root_u
        else:
            self.parent[root_v] = root_u
            self.rank[root_u] += 1

def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0 # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def cluster_reports_into_incidents(reports: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """
    Cluster reports into incidents using:
    - TF-IDF char_wb (3 to 5) cosine similarity
    - Geographic distance / overlap of uncertainty circles
    - Same need_type
    - Time window of 90 minutes
    - Union-find clustering
    """
    if not reports:
        return []
    if len(reports) == 1:
        return [reports]

    report_ids = [r["id"] for r in reports]
    uf = UnionFind(report_ids)

    # 1. TF-IDF char n-grams similarity matrix
    texts = [r.get("text", "") for r in reports]
    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(MERGE_CONFIG["tfidf_char_ngram_min"], MERGE_CONFIG["tfidf_char_ngram_max"])
    )
    tfidf_matrix = vectorizer.fit_transform(texts)
    sim_matrix = cosine_similarity(tfidf_matrix)

    time_window = MERGE_CONFIG["time_window_minutes"]
    geo_thresh = MERGE_CONFIG["geo_distance_meters_threshold"]
    sim_thresh = MERGE_CONFIG["text_similarity_threshold"]
    unres_thresh = MERGE_CONFIG["unresolved_text_similarity_threshold"]

    n = len(reports)
    for i in range(n):
        for j in range(i + 1, n):
            r1 = reports[i]
            r2 = reports[j]

            # Condition 1: Same need type (or one is 'other')
            need1 = r1.get("need_type")
            need2 = r2.get("need_type")
            same_need = (need1 == need2) or (need1 == "other" or need2 == "other")
            if not same_need:
                continue

            # Condition 2: Time window
            dt = abs(r1.get("minute", 0) - r2.get("minute", 0))
            if dt > time_window:
                continue

            # Condition 3: Text similarity
            text_sim = sim_matrix[i, j]

            # Check geographic compatibility
            has_geo1 = (r1.get("lat") is not None and r1.get("lon") is not None)
            has_geo2 = (r2.get("lat") is not None and r2.get("lon") is not None)

            if has_geo1 and has_geo2:
                # Both have coordinates: calculate physical distance
                dist = haversine_distance_m(r1["lat"], r1["lon"], r2["lat"], r2["lon"])
                max_radius = (r1.get("radius_m", 600.0) + r2.get("radius_m", 600.0))
                geo_match = (dist <= max(geo_thresh, max_radius))
                
                # If physical circle overlap AND (text similarity >= 0.25 or same zone)
                if geo_match and (text_sim >= 0.25 or r1.get("zone_id") == r2.get("zone_id")):
                    uf.union(r1["id"], r2["id"])
                elif text_sim >= sim_thresh:
                    uf.union(r1["id"], r2["id"])

            else:
                # Reports with unresolved location can merge only if same zone hint and high text similarity
                zone1 = r1.get("zone_id")
                zone2 = r2.get("zone_id")
                if zone1 and zone2 and zone1 == zone2:
                    if text_sim >= unres_thresh:
                        uf.union(r1["id"], r2["id"])
                else:
                    # No common zone, only union if text similarity is exceptionally high (e.g., exact copy-paste duplicate)
                    if text_sim >= 0.88:
                        uf.union(r1["id"], r2["id"])

    # Group into incident report lists
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in reports:
        root = uf.find(r["id"])
        if root not in groups:
            groups[root] = []
        groups[root].append(r)

    return list(groups.values())

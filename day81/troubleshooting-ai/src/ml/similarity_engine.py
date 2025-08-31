"""
ML-powered incident similarity and recommendation engine
"""
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import faiss
from typing import List, Dict, Tuple, Optional
import pickle
import os

from core.incident import Incident, Solution, Recommendation

class SimilarityEngine:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.sentence_model = SentenceTransformer(model_name)
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.incident_embeddings = []
        self.incidents = []
        self.solutions = []
        self.faiss_index = None
        
    def add_incident(self, incident: Incident, solution: Solution = None):
        """Add incident to the similarity database"""
        self.incidents.append(incident)
        if solution:
            self.solutions.append(solution)
        
        # Generate embedding
        text_features = incident.get_text_features()
        embedding = self.sentence_model.encode(text_features)
        self.incident_embeddings.append(embedding)
        
        # Rebuild FAISS index
        self._rebuild_index()
    
    def _rebuild_index(self):
        """Rebuild FAISS index for fast similarity search"""
        if len(self.incident_embeddings) == 0:
            return
            
        embeddings_array = np.array(self.incident_embeddings)
        dimension = embeddings_array.shape[1]
        
        # Use IndexFlatIP for cosine similarity
        self.faiss_index = faiss.IndexFlatIP(dimension)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings_array)
        self.faiss_index.add(embeddings_array)
    
    def find_similar_incidents(self, incident: Incident, top_k: int = 5) -> List[Tuple[Incident, float]]:
        """Find most similar historical incidents"""
        if self.faiss_index is None or len(self.incidents) == 0:
            return []
        
        # Generate embedding for query incident
        text_features = incident.get_text_features()
        query_embedding = self.sentence_model.encode([text_features])
        faiss.normalize_L2(query_embedding)
        
        # Search for similar incidents
        scores, indices = self.faiss_index.search(query_embedding, min(top_k, len(self.incidents)))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.incidents):
                results.append((self.incidents[idx], float(score)))
        
        return results
    
    def calculate_contextual_similarity(self, incident1: Incident, incident2: Incident) -> float:
        """Calculate contextual similarity beyond text matching"""
        context_score = 0.0
        
        # Service match
        if incident1.affected_service == incident2.affected_service:
            context_score += 0.3
        
        # Environment match
        if incident1.environment == incident2.environment:
            context_score += 0.2
        
        # Severity match
        if incident1.severity == incident2.severity:
            context_score += 0.1
        
        # Error type match
        if incident1.error_type == incident2.error_type:
            context_score += 0.4
        
        return min(context_score, 1.0)
    
    def recommend_solutions(self, incident: Incident, top_k: int = 3) -> List[Recommendation]:
        """Generate ranked solution recommendations"""
        similar_incidents = self.find_similar_incidents(incident, top_k * 2)
        
        if not similar_incidents:
            return []
        
        recommendations = []
        used_solutions = set()
        
        for similar_incident, similarity_score in similar_incidents:
            # Find solutions for this incident
            incident_solutions = [s for s in self.solutions if s.incident_id == similar_incident.id]
            
            for solution in incident_solutions:
                if solution.id in used_solutions:
                    continue
                
                used_solutions.add(solution.id)
                
                # Calculate contextual similarity
                context_match = self.calculate_contextual_similarity(incident, similar_incident)
                
                # Calculate final confidence score
                confidence = (
                    similarity_score * 0.4 +
                    context_match * 0.3 +
                    solution.effectiveness_score * 0.2 +
                    solution.success_rate * 0.1
                )
                
                recommendation = Recommendation(
                    solution=solution,
                    confidence_score=confidence,
                    similarity_score=similarity_score,
                    context_match=context_match,
                    reasoning=f"Similar incident: {similar_incident.title}",
                    similar_incidents=[similar_incident.id]
                )
                
                recommendations.append(recommendation)
                
                if len(recommendations) >= top_k:
                    break
            
            if len(recommendations) >= top_k:
                break
        
        return sorted(recommendations, key=lambda x: x.confidence_score, reverse=True)[:top_k]
    
    def save_model(self, filepath: str):
        """Save the trained model"""
        model_data = {
            'incidents': self.incidents,
            'solutions': self.solutions,
            'incident_embeddings': self.incident_embeddings
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self, filepath: str):
        """Load a trained model"""
        if not os.path.exists(filepath):
            return
            
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
            
        self.incidents = model_data['incidents']
        self.solutions = model_data['solutions']
        self.incident_embeddings = model_data['incident_embeddings']
        self._rebuild_index()

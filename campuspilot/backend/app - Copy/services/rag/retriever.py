import numpy as np


class Retriever:
    """Stores chunks with their vectors and finds the most relevant ones."""

    def __init__(self, embedder):
        self.embedder = embedder
        self.chunks = []      
        self.vectors = None   

    def add_chunks(self, chunks, filename):
        # Uploading the same file again replaces the old copy
        self.remove_document(filename)

        texts = [chunk["text"] for chunk in chunks]
        new_vectors = self.embedder.embed_texts(texts)

        # Remember which file each chunk came from (for citations)
        for chunk in chunks:
            self.chunks.append({**chunk, "source": filename})

        if self.vectors is None:
            self.vectors = new_vectors
        else:
            self.vectors = np.vstack([self.vectors, new_vectors])

    def list_documents(self):
        docs = {}
        for chunk in self.chunks:
            doc = docs.setdefault(
                chunk["source"], {"filename": chunk["source"], "chunks": 0, "pages": set()}
            )
            doc["chunks"] += 1
            doc["pages"].add(chunk["page"])
        return [
            {"filename": d["filename"], "chunks": d["chunks"], "pages": len(d["pages"])}
            for d in docs.values()
        ]

    def remove_document(self, filename):
        keep = [i for i, c in enumerate(self.chunks) if c["source"] != filename]
        if len(keep) == len(self.chunks):
            return False
        self.chunks = [self.chunks[i] for i in keep]
        self.vectors = self.vectors[keep] if keep else None
        return True

    def search(self, query, top_k=3):
        if not self.chunks:
            return []

        query_vector = self.embedder.embed_query(query)

        # Higher score = more similar in meaning
        scores = self.vectors @ query_vector

        # Indexes of the best scores, highest first
        best = np.argsort(scores)[::-1][:top_k]

        results = []
        for i in best:
            result = dict(self.chunks[i])
            result["score"] = round(float(scores[i]), 3)
            results.append(result)
        return results
class TextChunker:
    #Splits page text into small overlapping pieces (chunks).

    def __init__(self, chunk_size=1000, overlap=150):
        
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, pages):
        chunks = []

        for page in pages:
            text = page["text"]
            start = 0

            while start < len(text):
                end = start + self.chunk_size
                piece = text[start:end]

                chunks.append({
                    "page": page["page"],
                    "text": piece,
                    "chunk_index": len(chunks),
                })

                
                start = end - self.overlap

        return chunks
from difflib import SequenceMatcher

class KeywordFinder:
    def __init__(self, keywords):
        self.keywords = keywords

    def find_similar_keywords(self, target_keyword, threshold=0.5):
        similar_keywords = []
        for keyword in self.keywords:
            similarity = self._calculate_similarity(target_keyword, keyword)
            if similarity > threshold:
                similar_keywords.append(keyword)
        return similar_keywords

    def _calculate_similarity(self, a, b):
        return SequenceMatcher(None, a, b).ratio()
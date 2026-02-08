import json
import re
from collections import Counter
import textstat
import pandas as pd
 
with open("religious_texts_normalized.json", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)

  
def tokenize(text):
    return re.findall(r"[a-z']+", text.lower())

df["tokens"] = df["text"].apply(tokenize)


STOPWORDS = {
    "the","and","to","of","a","in","that","is","for","it","as","with","was","on",
    "be","by","are","this","which","or","from","at","his","her","their","they",
    "them","he","she","we","you","i","my","our","us","but","not","shall","must"
}

 
# N-gram helper
 
def make_ngrams(tokens, n):
    return zip(*(tokens[i:] for i in range(n)))

 
# Analysis per source
 
results = {}

for source, group in df.groupby("source"):
    all_tokens = [t for row in group["tokens"] for t in row]
    total_words = len(all_tokens)

    unique_words = set(all_tokens)
    unique_ratio = len(unique_words) / total_words if total_words else 0

     
    # Word frequency
     
    filtered = [w for w in all_tokens if w not in STOPWORDS]
    word_freq = Counter(filtered).most_common(20)

     
    # Phrase frequency
     
    bigrams = Counter(make_ngrams(filtered, 2)).most_common(15)
    trigrams = Counter(make_ngrams(filtered, 3)).most_common(15)

     
    # Command words
     
    full_text = " ".join(group["text"]).lower()

    command_counts = {
        "must": len(re.findall(r"\bmust\b", full_text)),
        "shall": len(re.findall(r"\bshall\b", full_text)),
        "do not": len(re.findall(r"\bdo not\b", full_text))
    }

     
    # Reading level
     
    reading_text = " ".join(group["text"])

    results[source] = {
        "total_words": total_words,
        "unique_words": len(unique_words),
        "unique_to_total_ratio": round(unique_ratio, 4),

        "flesch_reading_ease": round(textstat.flesch_reading_ease(reading_text), 2),
        "flesch_kincaid_grade": round(textstat.flesch_kincaid_grade(reading_text), 2),

        "most_frequent_words": word_freq,
        "most_frequent_bigrams": [
            {"phrase": " ".join(k), "count": v} for k, v in bigrams
        ],
        "most_frequent_trigrams": [
            {"phrase": " ".join(k), "count": v} for k, v in trigrams
        ],

        "command_word_counts": command_counts,
        "total_command_words": sum(command_counts.values())
    }

 
# Save analysis
 
with open("religious_texts_analysis.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("Analysis complete → religious_texts_analysis.json")

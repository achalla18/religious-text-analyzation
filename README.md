# Religious Text Analyzation

> A script pipeline that normalizes, analyzes, and visualizes linguistic patterns across five major religious texts — computing readability, lexical diversity, command word density, and phrase frequency per corpus.

---

## Text

The script processes five sources, producing one unified normalized dataset:

| Source Label | Text | Raw File |
|---|---|---|
| `Old Testament` | Hebrew Bible (KJV) | `old-testament.json` |
| `New Testament` | Christian New Testament (KJV) | `new-testament.json` |
| `Book of Mormon` | Latter-day Saint scripture | `book-of-mormon.json` |
| `Bhagavad Gita` | Hindu scripture (English translation) | `bg_en.json` |
| `Quran` | Islamic scripture (English translation) | `quran_en.json` |

### Data Sources

| Source | Repository |
|--------|------------|
| Old Testament, New Testament, Book of Mormon | [bcbooks/scriptures-json](https://github.com/bcbooks/scriptures-json) |
| Bhagavad Gita | [gita/gita](https://github.com/gita/gita) |
| Quran | [faisalill/quran_db](https://github.com/faisalill/quran_db) |

---

## Pipeline

The three scripts run in sequence. Each step depends on the results of the previous one.

```
refine.py  →  religious_texts_normalized.json
analyze.py →  religious_texts_analysis.json
visualize.py → images/*.png
```

---

### Step 1 — `refine.py`: Normalization

Each source uses a different JSON schema. `refine.py` reads all five raw files and flattens them into a single unified list of verse objects:

```python
{
  "source":  "Old Testament" | "New Testament" | "Book of Mormon" | "Bhagavad Gita" | "Quran",
  "book":    "Genesis" | "Al-Fatiha" | "Bhagavad Gita" | ...,
  "chapter": 1,
  "verse":   1,
  "text":    "In the beginning God created the heaven and the earth."
}
```

Each source is parsed differently to match its schema:

**Bible / Book of Mormon** (`bcbooks/scriptures-json` schema):
```
books[] → chapters[] → verses[] → { verse, text }
```
`book` is taken from `book["book"]`, `chapter` from `ch["chapter"]`, `verse` from `v["verse"]`, `text` from `v["text"]`.

**Bhagavad Gita** (`bg_en.json`):
Filters records where `v["lang"] == "english"` only. Maps `verse_id` → `chapter`, `verseNumber` → `verse`, `description` → `text`.

**Quran** (`quran_en.json`):
Iterates surahs, uses `surah["transliteration"]` as `book`, `surah["id"]` as `chapter`, and `v["translation"]` as `text`.

Empty or whitespace-only strings are dropped via the `add_row` guard:
```python
def add_row(source, book, chapter, verse, text):
    if text and text.strip():
        output.append({ ... })
```

Output: **`religious_texts_normalized.json`** — a flat list of all verses across all five corpora.

---

### Step 2 — `analyze.py`: Metric Computation

Loads `religious_texts_normalized.json` into a pandas DataFrame, then computes a set of metrics independently **per `source`** using `df.groupby("source")`.

#### Tokenization

```python
def tokenize(text):
    return re.findall(r"[a-z']+", text.lower())
```

Regex-based tokenization: lowercases input and extracts only sequences of `a-z` and apostrophes. This strips numbers, punctuation, and special characters. Applied to every row as `df["tokens"] = df["text"].apply(tokenize)`.

#### Stopword Removal

A hardcoded set of 37 high-frequency function words is used (not `nltk.corpus.stopwords`):

```python
STOPWORDS = {
    "the","and","to","of","a","in","that","is","for","it","as","with","was","on",
    "be","by","are","this","which","or","from","at","his","her","their","they",
    "them","he","she","we","you","i","my","our","us","but","not","shall","must"
}
```

Stopwords are only removed for frequency and n-gram analysis — **not** for readability or command word metrics, which operate on raw text.

#### Lexical Diversity

```python
unique_ratio = len(unique_words) / total_words
```

The type-token ratio (TTR): unique word types divided by total word tokens. Higher values indicate a wider, more varied vocabulary. Computed over the full corpus per source (not windowed).

#### Readability — Flesch–Kincaid Metrics

Uses the `textstat` library on the full joined text per source:

```python
textstat.flesch_reading_ease(reading_text)    # 0–100 scale; higher = easier
textstat.flesch_kincaid_grade(reading_text)   # US school grade level
```

Both metrics are based on average sentence length (ASL) and average syllables per word (ASW):

- **Flesch Reading Ease**: `206.835 − (1.015 × ASL) − (84.6 × ASW)`
- **Flesch–Kincaid Grade**: `(0.39 × ASL) + (11.8 × ASW) − 15.59`

These quantify accessibility — a higher grade level means longer sentences and more polysyllabic vocabulary.

#### N-gram Frequency

Bigrams and trigrams are generated with a sliding window zip pattern:

```python
def make_ngrams(tokens, n):
    return zip(*(tokens[i:] for i in range(n)))
```

Applied to the stopword-filtered token list. Top 20 unigrams, top 15 bigrams, and top 15 trigrams are returned per source using `Counter.most_common()`.

#### Command Word Density

Three imperative/obligation markers are counted via regex on the lowercased full text:

```python
command_counts = {
    "must":   len(re.findall(r"\bmust\b",   full_text)),
    "shall":  len(re.findall(r"\bshall\b",  full_text)),
    "do not": len(re.findall(r"\bdo not\b", full_text))
}
```

Word boundaries (`\b`) prevent partial matches. `total_command_words` is the sum across all three markers. `command_density` (computed in `visualize.py`) normalizes this by total word count.

#### Output Schema

```json
{
  "Old Testament": {
    "total_words": 123456,
    "unique_words": 12000,
    "unique_to_total_ratio": 0.0972,
    "flesch_reading_ease": 80.12,
    "flesch_kincaid_grade": 6.4,
    "most_frequent_words": [["lord", 7830], ["god", 4120], ...],
    "most_frequent_bigrams": [{"phrase": "lord god", "count": 312}, ...],
    "most_frequent_trigrams": [{"phrase": "lord thy god", "count": 145}, ...],
    "command_word_counts": {"must": 120, "shall": 4210, "do not": 398},
    "total_command_words": 4728
  },
  ...
}
```

Saved as **`religious_texts_analysis.json`**.

---

### Step 3 — `visualize.py`: Chart Generation

Loads `religious_texts_analysis.json` into a pandas DataFrame (transposed so each row is a source), then generates 8 chart types. All figures saved to `images/` using `sns.set_theme()` with `style="whitegrid"`, `context="talk"`, and spines disabled.

#### Charts Generated

**1. Reading Grade Level** (`reading_level_comparison.png`)
Bar chart of `flesch_kincaid_grade` per source. `palette="viridis"`.

**2. Lexical Diversity** (`lexical_complexity.png`)
Bar chart of `unique_to_total_ratio` per source. `palette="magma"`.

**3. Command Density** (`command_density.png`)
`command_density = total_command_words / total_words`. Bar chart per source. `palette="rocket"`.

**4. Complexity vs. Authority Scatter** (`complexity_vs_authority.png`)
Scatter plot with `unique_to_total_ratio` on the x-axis and `command_density` on the y-axis, colored by source. Shows whether texts that use richer vocabulary also use more or fewer imperative constructions.

**5. Z-score Heatmap** (`metric_heatmap.png`)
Standardizes three metrics — `flesch_kincaid_grade`, `unique_to_total_ratio`, `command_density` — to z-scores (mean 0, std 1) and renders a `coolwarm` annotated heatmap. Allows cross-metric comparison despite different scales.

```python
z_df = (z_input - z_input.mean()) / z_input.std(ddof=0)
```

**6. Top Words per Source** (`common_words_<source>.png`)
One horizontal bar chart per source showing the top 10 most frequent words after stopword removal. `palette="crest"`.

**7. Top Bigrams per Source** (`common_phrases_<source>.png`)
One horizontal bar chart per source showing the top 10 most frequent two-word phrases. `palette="flare"`.

**8. Summary Table** (`summary_table.png`)
A matplotlib table rendered as a figure with columns: `source`, `total_words`, `unique_words`, `unique_to_total_ratio`, `flesch_kincaid_grade`, `command_density`.

---

## Theory & Methodology

Each text is treated as a large natural language corpus. The goal is to surface statistical patterns — in vocabulary, readability, and rhetorical style — that are difficult to detect through manual reading alone. The same pipeline runs on all five sources so comparisons are fair.

### Preprocessing

Raw verse text is normalized before any analysis using regex tokenization (`re.findall(r"[a-z']+")`), which lowercases and strips punctuation in one pass. A hardcoded set of 37 stopwords removes high-frequency function words (`the`, `and`, `of`, etc.) that appear in every text and carry no distinguishing signal. Stopwords are only removed for frequency and n-gram analysis — readability and command word metrics run on raw text.

### Word Frequency & N-grams

The core assumption of corpus linguistics: words a text uses most often reflect what it is most *about*. We compute unigram, bigram, and trigram frequency distributions per source using `Counter` on the filtered token list. Bigrams and trigrams use a sliding-window zip pattern to capture meaningful phrases (`lord god`, `lord thy god`) that unigram analysis would miss entirely.

**Type-token ratio (TTR)** — `unique_words / total_words` — measures vocabulary richness. A higher TTR means the text draws from a wider, more varied vocabulary. Longer texts naturally have lower TTR due to repetition, so comparing TTR across the five corpora (which vary significantly in length) speaks to rhetorical style rather than just size.

### Readability — Flesch–Kincaid

Two readability scores are computed via `textstat` on the full joined text per source:

- **Flesch Reading Ease** — `206.835 − (1.015 × ASL) − (84.6 × ASW)` — 0 to 100 scale, higher means easier to read
- **Flesch–Kincaid Grade** — `(0.39 × ASL) + (11.8 × ASW) − 15.59` — maps to a US school grade level

Both use average sentence length (ASL) and average syllables per word (ASW). A higher grade level signals longer sentences and more polysyllabic vocabulary, which in this project reflects the complexity of each text's English translation rather than the original language.

### Command Word Density

Three imperative/obligation markers — `must`, `shall`, `do not` — are counted via `\b`-bounded regex on the lowercased full text, then normalized by total word count to produce a density score. This measures how directive or prescriptive each text is in tone. The scatter plot of command density vs. lexical diversity (`complexity_vs_authority.png`) explores whether texts with richer vocabulary also tend to use more imperative language, or whether the two are inversely related.

### Z-score Normalization

The three primary metrics — Flesch–Kincaid grade, TTR, and command density — operate on different scales and can't be directly compared as raw numbers. Z-score standardization transforms them to a common scale (mean 0, std 1), making the heatmap a true cross-metric, cross-source comparison where positive values indicate above-average and negative values indicate below-average for that metric.

```python
z_df = (z_input - z_input.mean()) / z_input.std(ddof=0)
```

---

## Setup & Usage

### 1. Clone

```bash
git clone https://github.com/achalla18/religious-text-analyzation.git
cd religious-text-analyzation
```

### 2. Install Dependencies

```bash
pip install pandas matplotlib seaborn textstat
```

### 3. Add Raw Data Files

Place the following in `scripts/` (or update the file paths in `refine.py`):

```
old-testament.json
new-testament.json
book-of-mormon.json
bg_en.json
quran_en.json
```

### 4. Run the Pipeline

```bash
cd scripts

python refine.py      # → religious_texts_normalized.json
python analyze.py     # → religious_texts_analysis.json
python visualize.py   # → images/*.png
```

---

## Dependencies

| Library | Purpose |
|---------|---------|
| `pandas` | DataFrame groupby, aggregation, z-score normalization |
| `matplotlib` | Figure rendering and table output |
| `seaborn` | Styled bar charts, scatter plots, heatmap |
| `textstat` | Flesch Reading Ease and Flesch–Kincaid Grade computation |
| `re` | Regex tokenization and command word pattern matching |
| `collections.Counter` | Unigram, bigram, trigram frequency ranking |
| `json` | Reading and writing all intermediate data files |

---

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.table import Table

 
# Folder setup
 
IMAGE_DIR = "images"
os.makedirs(IMAGE_DIR, exist_ok=True)

 
# Styling (publication-quality)
 
sns.set_theme(
    style="whitegrid",
    context="talk",
    font="DejaVu Sans",
    rc={
        "figure.dpi": 150,
        "axes.spines.top": False,
        "axes.spines.right": False
    }
)

 
# Load analysis data
 
with open("religious_texts_analysis.json", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data).T.reset_index()
df.rename(columns={"index": "source"}, inplace=True)

 
# Derived numeric metrics
 
df["command_density"] = df["total_command_words"] / df["total_words"]

 
# 1. Reading Level Comparison
 
plt.figure(figsize=(10, 6))
sns.barplot(
    data=df,
    x="source",
    y="flesch_kincaid_grade",
    palette="viridis"
)
plt.title("Reading Grade Level by Religious Text")
plt.ylabel("Flesch–Kincaid Grade Level")
plt.xlabel("")
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "reading_level_comparison.png"))
plt.close()

 
# 2. Lexical Complexity
 
plt.figure(figsize=(10, 6))
sns.barplot(
    data=df,
    x="source",
    y="unique_to_total_ratio",
    palette="magma"
)
plt.title("Lexical Complexity (Unique / Total Words)")
plt.ylabel("Lexical Diversity")
plt.xlabel("")
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "lexical_complexity.png"))
plt.close()

 
# 3. Command Density
 
plt.figure(figsize=(10, 6))
sns.barplot(
    data=df,
    x="source",
    y="command_density",
    palette="rocket"
)
plt.title("Command Word Density")
plt.ylabel("Commands per Word")
plt.xlabel("")
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "command_density.png"))
plt.close()

 
# 4. Complexity vs Authority
 
plt.figure(figsize=(9, 6))
sns.scatterplot(
    data=df,
    x="unique_to_total_ratio",
    y="command_density",
    hue="source",
    s=200
)
plt.title("Lexical Complexity vs Command Density")
plt.xlabel("Lexical Diversity")
plt.ylabel("Command Density")
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "complexity_vs_authority.png"))
plt.close()

 
# 5. Z-score Heatmap (SAFE numeric handling)
 
metrics = [
    "flesch_kincaid_grade",
    "unique_to_total_ratio",
    "command_density"
]

z_input = df[metrics].apply(pd.to_numeric, errors="coerce")
z_df = (z_input - z_input.mean()) / z_input.std(ddof=0)
z_df["source"] = df["source"]
z_df.set_index("source", inplace=True)

plt.figure(figsize=(10, 6))
sns.heatmap(
    z_df,
    annot=True,
    cmap="coolwarm",
    center=0
)
plt.title("Standardized Metric Comparison (Z-scores)")
plt.tight_layout()
plt.savefig(os.path.join(IMAGE_DIR, "metric_heatmap.png"))
plt.close()

 
# 6. Common Words (per text)
 
for _, row in df.iterrows():
    words = row["most_frequent_words"][:10]
    word_df = pd.DataFrame(words, columns=["word", "count"])

    plt.figure(figsize=(8, 5))
    sns.barplot(
        data=word_df,
        y="word",
        x="count",
        palette="crest"
    )
    plt.title(f"Most Common Words – {row['source']}")
    plt.tight_layout()
    plt.savefig(os.path.join(
        IMAGE_DIR,
        f"common_words_{row['source'].replace(' ', '_').lower()}.png"
    ))
    plt.close()

 
# 7. Common Phrases (Bigrams)
 
for _, row in df.iterrows():
    phrases = row["most_frequent_bigrams"][:10]
    phrase_df = pd.DataFrame(phrases)

    plt.figure(figsize=(9, 5))
    sns.barplot(
        data=phrase_df,
        y="phrase",
        x="count",
        palette="flare"
    )
    plt.title(f"Most Common Phrases – {row['source']}")
    plt.tight_layout()
    plt.savefig(os.path.join(
        IMAGE_DIR,
        f"common_phrases_{row['source'].replace(' ', '_').lower()}.png"
    ))
    plt.close()

 
# 8. Summary Table (as Image)
 
summary_cols = [
    "total_words",
    "unique_words",
    "unique_to_total_ratio",
    "flesch_kincaid_grade",
    "command_density"
]

summary_df = df[["source"] + summary_cols].round(4)

fig, ax = plt.subplots(figsize=(12, 3))
ax.axis("off")

table = ax.table(
    cellText=summary_df.values,
    colLabels=summary_df.columns,
    loc="center"
)

table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 1.5)

plt.title("Summary Metrics by Text", pad=20)
plt.savefig(os.path.join(IMAGE_DIR, "summary_table.png"), bbox_inches="tight")
plt.close()

 
# Done
 
print(f"All visualizations saved to ./{IMAGE_DIR}/")

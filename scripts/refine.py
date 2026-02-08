#Used to create a refined JSON file for easy analyzation


import json

output = []

def add_row(source, book, chapter, verse, text):
    if text and text.strip():
        output.append({
            "source": source,
            "book": book,
            "chapter": int(chapter),
            "verse": int(verse),
            "text": text.strip()
        })

#   OLD TESTAMENT  
with open("old-testament.json", encoding="utf-8") as f:
    data = json.load(f)

for book in data["books"]:
    book_name = book["book"]
    for ch in book["chapters"]:
        chapter_num = ch["chapter"]
        for v in ch["verses"]:
            add_row(
                "Old Testament",
                book_name,
                chapter_num,
                v["verse"],
                v["text"]
            )

#   NEW TESTAMENT  
with open("new-testament.json", encoding="utf-8") as f:
    data = json.load(f)

for book in data["books"]:
    book_name = book["book"]
    for ch in book["chapters"]:
        for v in ch["verses"]:
            add_row(
                "New Testament",
                book_name,
                ch["chapter"],
                v["verse"],
                v["text"]
            )

#   BOOK OF MORMON  
with open("book-of-mormon.json", encoding="utf-8") as f:
    data = json.load(f)

for book in data["books"]:
    book_name = book["book"]
    for ch in book["chapters"]:
        for v in ch["verses"]:
            add_row(
                "Book of Mormon",
                book_name,
                ch["chapter"],
                v["verse"],
                v["text"]
            )

#   BHAGAVAD GITA  
with open("bg_en.json", encoding="utf-8") as f:
    data = json.load(f)

for v in data:
    if v.get("lang") == "english":
        add_row(
            "Bhagavad Gita",
            "Bhagavad Gita",
            v["verse_id"],
            v["verseNumber"],
            v["description"]
        )

#   QURAN  
with open("quran_en.json", encoding="utf-8") as f:
    data = json.load(f)

for surah in data:
    surah_name = surah["transliteration"]
    surah_id = surah["id"]
    for v in surah["verses"]:
        add_row(
            "Quran",
            surah_name,
            surah_id,
            v["id"],
            v["translation"]
        )

#   SAVE  
with open("religious_texts_normalized.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"Saved {len(output)} verses to religious_texts_normalized.json")

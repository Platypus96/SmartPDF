import fitz
import json
import os
from collections import defaultdict

def extract_outline(pdf_path):
    doc = fitz.open(pdf_path)

    # Extract title from first page
    title = extract_title(doc[0])

    # Try to get document outline (table of contents)
    toc = doc.get_toc()
    if toc:
        outline = process_toc(toc)
        return {"title": title, "outline": outline}

    # Fallback to heading extraction from document structure
    raw_outline = extract_headings(doc)
    corrected_outline = enforce_heading_order(raw_outline)
    return {"title": title, "outline": corrected_outline}

def extract_title(page):
    """Extract title from top 30% of first page"""
    top_threshold = page.rect.height * 0.3
    blocks = page.get_text("dict")["blocks"]

    candidates = []
    for block in blocks:
        if block['type'] == 0:
            for line in block["lines"]:
                if not line["spans"]:
                    continue
                max_font = max(span['size'] for span in line["spans"])
                text = ''.join(span['text'] for span in line["spans"]).strip()
                if text and line["bbox"][1] < top_threshold:
                    candidates.append((text, max_font, line["bbox"]))

    if candidates:
        return max(candidates, key=lambda x: x[1])[0]

    for block in blocks:
        if block['type'] == 0:
            for line in block["lines"]:
                text = ''.join(span['text'] for span in line["spans"]).strip()
                if text:
                    return text
    return "Untitled"

def process_toc(toc):
    outline = []
    for entry in toc:
        level = entry[0]
        if level > 3:
            continue
        outline.append({
            "level": f"H{level}",
            "text": entry[1],
            "page": entry[2]
        })
    return outline

def extract_headings(doc):
    heading_styles = identify_heading_styles(doc)
    outline = []

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block['type'] != 0:
                continue
            for line in block["lines"]:
                if not line["spans"]:
                    continue
                span = line["spans"][0]
                style_signature = (
                    round(span['size']),
                    span['font'].lower(),
                    span['flags'] & 2
                )
                if style_signature in heading_styles:
                    text = ''.join(s['text'] for s in line["spans"]).strip()
                    if text:
                        outline.append({
                            "level": heading_styles[style_signature],
                            "text": text,
                            "page": page_num + 1
                        })

    return outline

def enforce_heading_order(outline):
    """Ensure H2 does not appear before H1, H3 not before H2"""
    has_seen = {"H1": False, "H2": False}
    corrected = []

    for item in outline:
        level = item["level"]

        if level == "H2" and not has_seen["H1"]:
            # Downgrade to H1
            item["level"] = "H1"
        elif level == "H3" and not has_seen["H2"]:
            if has_seen["H1"]:
                item["level"] = "H2"
            else:
                item["level"] = "H1"

        has_seen[item["level"]] = True
        corrected.append(item)

    return corrected

def identify_heading_styles(doc):
    style_counter = defaultdict(int)

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block['type'] != 0:
                continue
            for line in block["lines"]:
                if not line["spans"]:
                    continue
                span = line["spans"][0]
                signature = (
                    round(span['size']),
                    span['font'].lower(),
                    span['flags'] & 2
                )
                style_counter[signature] += 1

    common_styles = set()
    if style_counter:
        sorted_styles = sorted(style_counter.items(), key=lambda x: x[1], reverse=True)
        common_styles = set(style[0] for style in sorted_styles[:3])

    heading_candidates = {}
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block['type'] != 0:
                continue
            for line in block["lines"]:
                if not line["spans"]:
                    continue
                span = line["spans"][0]
                signature = (
                    round(span['size']),
                    span['font'].lower(),
                    span['flags'] & 2
                )
                if signature in common_styles:
                    continue
                text = ''.join(s['text'] for s in line["spans"]).strip()
                if text and len(text) < 150:
                    heading_candidates[signature] = heading_candidates.get(signature, 0) + 1

    heading_styles = {}
    if heading_candidates:
        sorted_headings = sorted(heading_candidates.items(), key=lambda x: (x[0][0], x[1]), reverse=True)
        for i, (signature, _) in enumerate(sorted_headings[:3]):
            heading_styles[signature] = f"H{i+1}"

    return heading_styles

def main():
    input_dir = "/app/input"
    output_dir = "/app/output"
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_dir, filename)
            result = extract_outline(pdf_path)
            output_path = os.path.join(output_dir, filename.replace(".pdf", ".json"))
            with open(output_path, 'w', encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()

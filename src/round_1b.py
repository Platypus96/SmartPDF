import json
import os
import torch
from sentence_transformers import SentenceTransformer, util
from datetime import datetime

# Import the function from your Round 1A script
from round_1a import analyze_pdf_structure

def find_relevant_sections(doc_collection, persona_query):
    """
    Finds and ranks document sections based on semantic similarity to a query.
    """
    # 1. Load the pre-cached sentence transformer model
    model_path = '/app/model_cache/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/c9745ed1d9f207416be6d2e6f8de32d1f16199bf'
    model = SentenceTransformer(model_path, device='cpu')

    # 2. Create embeddings for all document sections, ensuring no duplicates
    sections = []
    seen_titles = set() # Use a set to track titles we've already added

    for filename, data in doc_collection.items():
        if "outline" not in data:
            continue
        for heading in data["outline"]:
            title = heading["text"]
            # --- Deduplication Step ---
            # If we have already processed this title, skip it
            if title.lower() in seen_titles:
                continue
            
            seen_titles.add(title.lower())
            
            text_to_embed = f'{data["title"]} {title}'
            sections.append({
                "document": filename,
                "page": heading["page"],
                "title": title,
                "text_to_embed": text_to_embed
            })
    
    if not sections:
        return []

    corpus_embeddings = model.encode([s["text_to_embed"] for s in sections], convert_to_tensor=True)

    # 3. Create embedding for the persona query
    query_embedding = model.encode(persona_query, convert_to_tensor=True)

    # 4. Calculate cosine similarity
    cos_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]

    # 5. Rank the results
    top_results = torch.topk(cos_scores, k=min(len(sections), 10))

    ranked_sections = []
    for i, (score, idx) in enumerate(zip(top_results[0], top_results[1])):
        section = sections[idx]
        ranked_sections.append({
            "document": section["document"],
            "page_number": section["page"],
            "section_title": section["title"],
            "importance_rank": i + 1
        })
        
    return ranked_sections

# The main() function remains the same as before
def main():
    input_dir = "/app/input"
    output_dir = "/app/output"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load persona and job description
    try:
        with open(os.path.join(input_dir, "persona.json"), "r") as f:
            persona_data = json.load(f)
        persona_query = f"{persona_data['persona']['role']}. {persona_data['job_to_be_done']}"
    except FileNotFoundError:
        print("Error: persona.json not found in the input directory.")
        return

    # Process all PDFs using the 1A logic
    doc_collection = {}
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]
    for filename in pdf_files:
        pdf_path = os.path.join(input_dir, filename)
        print(f"Analyzing structure of {filename}...")
        doc_collection[filename] = analyze_pdf_structure(pdf_path)

    # Find the most relevant sections across all documents
    print("Finding relevant sections...")
    extracted_sections = find_relevant_sections(doc_collection, persona_query)

    # Format the final output JSON
    output_data = {
        "metadata": {
            "input_documents": pdf_files,
            "persona": persona_data["persona"],
            "job_to_be_done": persona_data["job_to_be_done"],
            "processing_timestamp": datetime.utcnow().isoformat() + "Z"
        },
        "extracted_sections": extracted_sections,
        "sub_section_analysis": [] 
    }
    
    output_path = os.path.join(output_dir, "challenge1b_output.json")
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=4)
        
    print(f"Successfully generated 1B output at {output_path}")

if __name__ == "__main__":
    main()
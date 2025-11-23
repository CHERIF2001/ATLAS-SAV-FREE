import pandas as pd
from pathlib import Path

data_file = Path("data/processed/tweets_enriched.parquet")
if data_file.exists():
    df = pd.read_parquet(data_file)
    print("Columns:", df.columns.tolist())
    if "motif" in df.columns:
        print("Found 'motif' (lowercase)")
    if "Motif" in df.columns:
        print("Found 'Motif' (Capitalized)")
    
    # Check for other columns
    print("Sentiment column:", [c for c in df.columns if "sentiment" in c.lower()])
else:
    print("File not found!")

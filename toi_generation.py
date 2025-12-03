#!/usr/bin/env python3
import glob
import pandas as pd

ROOT_TERMS = {
    "GO:0008150",  # BP root
    "GO:0003674",  # MF root
    "GO:0005575",  # CC root
}

terms = set()

for fname in glob.glob("clean-repo/gt_all/gt_all.*.tsv"):
    df = pd.read_csv(fname, sep="\t", dtype=str)
    if "go_term" not in df.columns:
        raise ValueError(f"Falta columna 'go_term' en {fname}")
    terms.update(df["go_term"].dropna().unique())

terms = {t for t in terms if t not in ROOT_TERMS}

with open("terms_of_interest.txt", "w") as f:
    for term in sorted(terms):
        f.write(term + "\n")

print(f"Escritos {len(terms)} términos en terms_of_interest.txt")

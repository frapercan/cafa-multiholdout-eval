#!/usr/bin/env python3
import argparse
import os
import sys
import pandas as pd

# Evidencias que cuentan para known y ground truth
EXP_CODES = {
    "EXP", "IDA", "IPI", "IMP", "IGI", "IEP",
    "HTP", "HDA", "HMP", "HGI", "HEP", "IC", "TAS"
}


def find_snapshot_file(n: int, base_path: str) -> str:
    """
    Intenta localizar el fichero del snapshot N en dos formatos:

    1) base_path/goa_uniprot_all_subset.N.tsv
    2) base_path/goa_uniprot_all.gaf.N/goa_uniprot_all_subset.N.tsv
    """
    candidates = [
        os.path.join(base_path, f"goa_uniprot_all_subset.{n}.tsv"),
        os.path.join(base_path, f"goa_uniprot_all.gaf.{n}", f"goa_uniprot_all_subset.{n}.tsv"),
    ]
    for fname in candidates:
        if os.path.exists(fname):
            return fname

    raise FileNotFoundError(
        f"No se encontró el snapshot {n} en ninguna de estas rutas:\n"
        + "\n".join(candidates)
    )


def load_snapshot(n: int, base_path: str) -> pd.DataFrame:
    """
    Carga el snapshot N (formato detectado automáticamente).
    """
    fname = find_snapshot_file(n, base_path)
    print(f"  - Cargando snapshot {n} desde: {fname}")
    df = pd.read_csv(fname, sep="\t", comment="!", dtype=str)

    required = {"protein_id", "go_term", "evidence_code"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Al snapshot {n} le faltan columnas requeridas: {', '.join(sorted(missing))}"
        )
    return df


def get_exp_rows(df: pd.DataFrame, codes=EXP_CODES) -> pd.DataFrame:
    """
    Filtra filas con evidencias de interés y DESCARTA qualifiers con NOT.

    - evidence_code ∈ codes
    - qualifier NO contiene NOT como token GAF (NOT, NOT|..., ...|NOT|...)
    """
    # Filtrar por evidencias EXP/curadas
    mask_exp = df["evidence_code"].isin(codes)

    # Si no existe la columna 'qualifier', asumimos que no hay NOT
    if "qualifier" in df.columns:
        q = df["qualifier"].fillna("")
        # detectar NOT como token separado en qualifiers tipo GAF
        mask_not = q.str.contains(r"(?:^|\|)NOT(?:\||$)", regex=True)
        mask_ok = ~mask_not
    else:
        mask_ok = True

    exp_df = df.loc[mask_exp & mask_ok].copy()
    exp_df = exp_df.dropna(subset=["protein_id", "go_term"])
    return exp_df


def build_holdout_sets(dfN: pd.DataFrame,
                       dfNp1: pd.DataFrame,
                       codes=EXP_CODES):
    """
    A partir de dos snapshots consecutivos N y N+1 genera:

    - known_N:
        todas las anotaciones EXP/curadas (sin NOT) de N
        (todas las columnas, sin duplicados exactos).

    - gt_all_Np1:
        todas las anotaciones EXP/curadas (sin NOT) de N+1
        (todas las columnas, sin duplicados exactos).

    - gt_new_pairs:
        SOLO pares nuevos N+1 \ N a nivel (protein_id, go_term),
        con todas las columnas de N+1.
    """
    expN = get_exp_rows(dfN, codes)
    expNp1 = get_exp_rows(dfNp1, codes)

    known_N = expN.drop_duplicates()
    gt_all_Np1 = expNp1.drop_duplicates()

    # Pares proteína–GO en N y N+1
    pairsN = expN[["protein_id", "go_term"]].drop_duplicates()
    pairsNp1 = expNp1[["protein_id", "go_term"]].drop_duplicates()

    # Anti-join: pares que aparecen en N+1 pero no en N
    merged = pairsNp1.merge(
        pairsN,
        on=["protein_id", "go_term"],
        how="left",
        indicator=True,
    )
    new_pairs = merged[merged["_merge"] == "left_only"][["protein_id", "go_term"]]

    # ground truth "new-only" = filas completas de N+1 correspondientes a esos pares nuevos
    gt_new_pairs = new_pairs.merge(
        expNp1,
        on=["protein_id", "go_term"],
        how="left"
    ).drop_duplicates()

    return known_N, gt_all_Np1, gt_new_pairs


def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Construye conjuntos known, gt_all (N+1) y ground_truth_new (N+1 \\ N) "
            "para CAFA5, listos para evaluación Partial Knowledge con CAFA-evaluator."
        )
    )
    parser.add_argument(
        "--base-path",
        type=str,
        default=".",
        help="Ruta base donde están los GAF (carpetas goa_uniprot_all.gaf.N/ o TSV sueltos)."
    )
    parser.add_argument(
        "--start",
        type=int,
        default=214,
        help="Primer snapshot (N) a usar (por defecto: 214)."
    )
    parser.add_argument(
        "--end",
        type=int,
        default=225,
        help=(
            "Último snapshot N para el que se generará N→N+1. "
            "Con end=225 se genera 214→215, ..., 225→226."
        )
    )
    parser.add_argument(
        "--out-known-dir",
        type=str,
        default="known",
        help="Directorio de salida para known.N.tsv"
    )
    parser.add_argument(
        "--out-gtall-dir",
        type=str,
        default="gt_all",
        help="Directorio de salida para gt_all.Nplus1.tsv"
    )
    parser.add_argument(
        "--out-gtnew-dir",
        type=str,
        default="ground_truth",
        help="Directorio de salida para ground_truth.N_Nplus1.tsv (solo pares nuevos)"
    )

    args = parser.parse_args()

    base_path = args.base_path
    start = args.start
    end = args.end

    if end < start:
        print("ERROR: end debe ser ≥ start", file=sys.stderr)
        sys.exit(1)

    ensure_dir(args.out_known_dir)
    ensure_dir(args.out_gtall_dir)
    ensure_dir(args.out_gtnew_dir)

    print(
        f"Usando snapshots desde {start} hasta {end+1} "
        f"(generando N→N+1 para {start}…{end})"
    )

    for n in range(start, end + 1):
        n_next = n + 1
        print(f"\n=== Procesando N={n} → N+1={n_next} ===")
        try:
            dfN = load_snapshot(n, base_path)
            dfNp1 = load_snapshot(n_next, base_path)

            known_N, gt_all_Np1, gt_new_pairs = build_holdout_sets(dfN, dfNp1)

            out_known = os.path.join(args.out_known_dir, f"known.{n}.tsv")
            out_gtall = os.path.join(args.out_gtall_dir, f"gt_all.{n_next}.tsv")
            out_gtnew = os.path.join(args.out_gtnew_dir, f"ground_truth.{n}_{n_next}.tsv")

            known_N.to_csv(out_known, sep="\t", index=False)
            gt_all_Np1.to_csv(out_gtall, sep="\t", index=False)
            gt_new_pairs.to_csv(out_gtnew, sep="\t", index=False)

            print(
                f"  - known: {out_known} "
                f"(filas={len(known_N)}, proteínas={known_N['protein_id'].nunique()})"
            )
            print(
                f"  - gt_all: {out_gtall} "
                f"(filas={len(gt_all_Np1)}, proteínas={gt_all_Np1['protein_id'].nunique()})"
            )
            print(
                f"  - ground_truth_new: {out_gtnew} "
                f"(filas={len(gt_new_pairs)}, proteínas={gt_new_pairs['protein_id'].nunique()})"
            )

        except Exception as e:
            print(f"[ERROR] Al procesar N={n} → {n_next}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()

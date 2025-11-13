#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys


def run_snapshot(
    n: int,
    ontology_file: str,
    submission_dir: str,
    gtdelta_dir: str,
    known_dir: str,
    toi_file: str | None,
    out_root: str,
    cafaeval_entry: str,
    threads: int,
    th_step: float,
    ia_file: str | None,   # ← NUEVO
):
    """
    Lanza CAFA-evaluator para un snapshot N → N+1 usando:

      - ground truth delta (solo nuevos):
            ground_truth/ground_truth.N_Nplus1.tsv
      - known:
            known/known.N.tsv
      - predicciones: carpeta 'submission_dir'

    Incluye por defecto:
      -max_terms 500 -prop fill -norm cafa -no_orphans -threads <threads> -th_step <th_step>

    Soporta TOI e IA.
    """
    n_next = n + 1

    # GT delta: solo pares nuevos N+1 \ N
    gt_file = os.path.join(gtdelta_dir, f"ground_truth.{n}_{n_next}.tsv")
    known_file = os.path.join(known_dir, f"known.{n}.tsv")

    if not os.path.exists(gt_file):
        print(
            f"[WARN] No existe ground truth delta para {n}->{n_next}: {gt_file}",
            file=sys.stderr,
        )
        return

    if not os.path.exists(known_file):
        print(f"[WARN] No existe known para {n}: {known_file}", file=sys.stderr)
        return

    out_dir = os.path.join(out_root, f"{n}_{n_next}")
    os.makedirs(out_dir, exist_ok=True)

    # Construir comando base
    if cafaeval_entry == "module":
        cmd = [
            sys.executable,
            "-m",
            "cafaeval",
            ontology_file,
            submission_dir,
            gt_file,
            "-known",
            known_file,
            "-out_dir",
            out_dir,
        ]
    else:
        cmd = [
            sys.executable,
            cafaeval_entry,
            ontology_file,
            submission_dir,
            gt_file,
            "-known",
            known_file,
            "-out_dir",
            out_dir,
        ]

    # Opciones por defecto
    cmd.extend(
        [
            "-max_terms",
            "500",
            "-prop",
            "fill",
            "-norm",
            "cafa",
            "-no_orphans",
            "-threads",
            str(threads),
            "-th_step",
            str(th_step),
        ]
    )

    # TOI opcional
    if toi_file is not None:
        cmd.extend(["-toi", toi_file])

    # IA opcional (NUEVO)
    if ia_file is not None:
        cmd.extend(["-ia", ia_file])

    print(f"\n>>> Evaluando snapshot N={n} → N+1={n_next} (delta)")
    print("    GT (delta):", gt_file)
    print("    KNOWN     :", known_file)
    print("    PRED      :", submission_dir)
    print("    OUT       :", out_dir)
    print("    CMD       :", " ".join(cmd))

    subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Evalúa una submission CAFA frente a múltiples holdouts N→N+1 "
            "usando ground_truth delta (N+1 \\ N) + known (Partial Knowledge)."
        )
    )
    parser.add_argument(
        "--ontology",
        required=True,
        help="Fichero de ontología en formato OBO (p.ej. go-basic.obo).",
    )
    parser.add_argument(
        "--submission-dir",
        default="submission",
        help="Carpeta que contiene submission.tsv (formato CAFA).",
    )
    parser.add_argument(
        "--gtdelta-dir",
        default="ground_truth",
        help="Directorio con ground_truth.N_Nplus1.tsv (solo nuevos).",
    )
    parser.add_argument(
        "--known-dir",
        default="known",
        help="Directorio con known.N.tsv (anotaciones conocidas en N).",
    )
    parser.add_argument(
        "--toi",
        default=None,
        help="Fichero con terms-of-interest (TOI).",
    )
    parser.add_argument(
        "--ia",
        default=None,
        help="Information Accretion file (IA). Ej: IA.txt",
    )
    parser.add_argument(
        "--out-root",
        default="results_submission_delta",
        help="Directorio raíz de salida para los resultados.",
    )
    parser.add_argument(
        "--start",
        type=int,
        required=True,
        help="Primer snapshot N a evaluar.",
    )
    parser.add_argument(
        "--end",
        type=int,
        required=True,
        help="Último snapshot N a evaluar.",
    )
    parser.add_argument(
        "--cafaeval-entry",
        default="module",
        help="Cómo invocar CAFA-evaluator: 'module' o ruta a __main__.py.",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=4,
        help="Número de hilos (-threads). 0 = todos.",
    )
    parser.add_argument(
        "--th-step",
        type=float,
        default=0.01,
        help="Paso de umbral (-th_step). Subirlo acelera la evaluación.",
    )

    args = parser.parse_args()

    if args.end < args.start:
        print("ERROR: --end debe ser ≥ --start", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.ontology):
        print(f"ERROR: Ontology file no existe: {args.ontology}", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(args.submission_dir):
        print(
            f"ERROR: submission-dir no existe o no es carpeta: {args.submission_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    has_tsv = any(fname.endswith(".tsv") for fname in os.listdir(args.submission_dir))
    if not has_tsv:
        print(
            f"ERROR: no se encontró ningún .tsv dentro de {args.submission_dir}.",
            file=sys.stderr,
        )
        sys.exit(1)

    os.makedirs(args.out_root, exist_ok=True)

    print(
        f"Evaluando snapshots delta {args.start}→{args.start+1} ... {args.end}→{args.end+1}"
    )

    for n in range(args.start, args.end + 1):
        try:
            run_snapshot(
                n=n,
                ontology_file=args.ontology,
                submission_dir=args.submission_dir,
                gtdelta_dir=args.gtdelta_dir,
                known_dir=args.known_dir,
                toi_file=args.toi,
                out_root=args.out_root,
                cafaeval_entry=args.cafaeval_entry,
                threads=args.threads,
                th_step=args.th_step,
                ia_file=args.ia,  # ← NUEVO
            )
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] CAFA-evaluator falló para N={n}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()

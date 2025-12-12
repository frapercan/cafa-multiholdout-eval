
# CAFA Multi-Holdout Evaluator

This repository provides a simple workflow to evaluate CAFA submissions across multiple holdouts.

---

## 1. Environment Setup

The environment must include:

- **pandas**
- **CAFA-evaluator-PK**

You may install CAFA-evaluator:


### Install locally (editable mode)

If the package is already copied in the project root:

```bash
pip install pandas
pip install -e CAFA-evaluator-PK
```
or
```bash
poetry install
```

---

## 2. Preparing the Submission

Place your CAFA-formatted `.tsv` file inside:

```text
submissions/
```

This directory must contain at least one valid CAFA prediction file.

---

## 3. Running the Evaluator (snapshot range mode)

(I ensembled 227–228 into 227 in order to not change the program behaviour)

To run the multi-holdout evaluation using snapshot ranges:

```bash
python3 evaluate_submission_holdout.py \
    --ontology go-basic.obo \
    --submission-dir submissions \
    --gtdelta-dir ground_truth \
    --known-dir known \
    --start 226 \
    --end 227 \
    --ia IA.tsv \
    --th-step 0.1
```

This executes the evaluations for snapshots **226 → 227** and **227 → 228**.

---

## 4. Running the Evaluator (single merged ground truth, no ranges)

Alternatively, you can run a **single evaluation without snapshot ranges**, using an explicit ground truth and known file.

This is useful when working with a merged ground truth such as:

```text
ground_truth/ground_truth.227_228.merged.tsv
```

Run:

```bash
python3 evaluate_submission_holdout.py \
    --ontology go-basic.obo \
    --submission-dir submissions \
    --gt-file ground_truth/ground_truth.227_228.merged.tsv \
    --known-file known/known.226.tsv \
    --ia IA.tsv \
    --th-step 0.1
```

In this mode:

* `--start` and `--end` are **not used**
* The evaluation is executed **once**
* The output directory is derived from the ground truth filename

---

## 5. Required Files

Ensure the following files and directories are present:

```text
submissions/
ground_truth/
known/
go-basic.obo
```

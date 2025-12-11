# **CAFA Multi-Holdout Evaluator**

This repository provides a simple workflow to evaluate CAFA submissions across multiple holdouts.

---

## **1. Environment Setup**

The environment must include:

* **pandas**
* **CAFA-evaluator-PK**

You may install CAFA-evaluator-PK in two ways:

### **Install from PyPI**

```bash
pip install cafa-evaluator-pk
```

### **Install locally (editable mode)**

If the package is already copied in the project root:

```bash
pip install -e CAFA-evaluator-PK-main
```

---

## **2. Preparing the Submission**

Place your CAFA-formatted `.tsv` file inside:

```
submissions/
```

This directory must contain at least one valid CAFA prediction file.

---

## **3. Running the Evaluator**
(I ensembled 227-228 into 227, in order to not change the programs behaviour)
To run the multi-holdout evaluation:

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

## **4. Required Files**

Ensure the following directories contain the appropriate files:

```
ground_truth/
known/
submissions/
go-basic.obo
```


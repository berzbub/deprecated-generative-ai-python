# Medicine Catalog — Feature Implementation

## Overview

This document tracks the implementation of the AI-powered Medicine Catalog feature
requested in the project issue.

## Feature Requirements & Status

### Core Catalog
- [x] Medicine catalog data sorted **alphabetically by health problem**
- [x] Each entry includes:
  - Common name and **scientific name**
  - Brand names / trade names
  - Effects / therapeutic use
  - **Contraindications**
  - Image URL reference
- [x] **Global equivalents** — conventional drugs and medicinal plants from different
  countries/regions (Philippines, India, China/TCM, Africa, Europe, Middle East, etc.)
  with local plant names and notes

### AI-Powered Features
- [x] **AI catalog lookup** — text-based Q&A using the sorted catalog as context
- [x] **Emergency / First-Aid Diagnosis** — structured system prompt guides AI to provide
  calm, actionable first-aid steps and direct users to emergency services
- [x] **Emotional State Detection** — system instruction instructs the model to detect
  signs of fear, anxiety, or distress and respond with a soothing, empathetic tone
  *before* providing clinical information
- [x] **Structured Symptom Interview** — the model asks one focused question at a time,
  gathers at least 4-5 responses, then summarises the likely concern and next steps
- [x] **Patient Health Record Analysis** — accepts free-text health records (vitals, labs,
  medications, allergies) and returns a structured summary with abnormal findings and
  follow-up recommendations
- [x] **Multimodal Medicine Identification** — uses Gemini's vision capability to identify
  a medicine or medicinal plant from an image

## File Location

`samples/medicine_catalog.py`

## Covered Health Problems (sorted A–Z)

| Health Problem                 | Medicine Class     | Example Drug        |
|--------------------------------|--------------------|---------------------|
| Anxiety                        | Anxiolytic         | Diazepam            |
| Fever                          | Antipyretic        | Paracetamol         |
| Headache                       | NSAID / Analgesic  | Ibuprofen           |
| Hypertension (High Blood Pres.)| Antihypertensive   | Amlodipine          |
| Infection (Bacterial)          | Antibiotic         | Amoxicillin         |
| Nausea / Vomiting              | Antiemetic         | Metoclopramide      |
| Wound / Skin Infection         | Topical Antiseptic | Povidone-Iodine     |

## Disclaimer

All information provided by the AI assistant is for **educational purposes only**.
It is **not** a substitute for professional medical advice, diagnosis, or treatment.
Users are always reminded to consult a qualified healthcare provider.

## Running the Sample Tests

```bash
python -m pytest samples/medicine_catalog.py -v
# or
python samples/medicine_catalog.py
```

> **Note:** Tests that call the Gemini API require a valid `GOOGLE_API_KEY`
> environment variable. The `test_catalog_sorted_alphabetically` test runs fully
> offline and validates the sorting logic.

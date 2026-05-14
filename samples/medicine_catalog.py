# -*- coding: utf-8 -*-
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Medicine Catalog sample using Google Generative AI.

This module demonstrates:
- An AI-powered medicine/remedy catalog sorted alphabetically by health problem.
- Scientific names, effects, contraindications, and global equivalents
  (conventional drugs and medicinal plants from different countries/regions).
- Image-based medicine identification (multimodal).
- AI-assisted first-aid and emergency diagnosis.
- Emotionally-aware patient interaction: detecting fear/anxiety and
  responding with a soothing, analytical interview approach.
- Patient health record reading and analysis.

DISCLAIMER: This sample is for educational and demonstration purposes only.
It is NOT a substitute for professional medical advice, diagnosis, or treatment.
Always consult a qualified healthcare provider before acting on any
information provided by this system.
"""

from absl.testing import absltest
import pathlib

media = pathlib.Path(__file__).parents[1] / "third_party"

# ---------------------------------------------------------------------------
# Inline catalog data
# (In a production system this would live in a database or JSON file.)
# ---------------------------------------------------------------------------
MEDICINE_CATALOG = [
    {
        "health_problem": "Anxiety",
        "scientific_category": "Anxiolytic",
        "medicines": [
            {
                "common_name": "Diazepam",
                "scientific_name": "7-chloro-1-methyl-5-phenyl-3H-benzo[e][1,4]diazepin-2(1H)-one",
                "brand_names": ["Valium"],
                "effects": "Reduces anxiety, muscle spasms, and seizures by enhancing GABA activity.",
                "contraindications": [
                    "Respiratory depression",
                    "Myasthenia gravis",
                    "Alcohol dependence",
                    "Pregnancy (especially 1st trimester)",
                ],
                "global_equivalents": [
                    {
                        "country_region": "Southeast Asia / Philippines",
                        "plant": "Passiflora incarnata (Passion flower)",
                        "local_name": "Pasionaria",
                        "notes": "Mild sedative used as herbal tea.",
                    },
                    {
                        "country_region": "Europe / Germany",
                        "plant": "Valeriana officinalis (Valerian root)",
                        "local_name": "Baldrian",
                        "notes": "OTC sleep and anxiety aid.",
                    },
                    {
                        "country_region": "India / Ayurveda",
                        "plant": "Withania somnifera (Ashwagandha)",
                        "local_name": "Ashwagandha",
                        "notes": "Adaptogen that reduces cortisol and anxiety.",
                    },
                ],
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/Diazepam_2mg_5mg_tablets.jpg/320px-Diazepam_2mg_5mg_tablets.jpg",
                "first_aid_notes": (
                    "Overdose: ensure airway is open, lay patient on their side, "
                    "call emergency services. Do NOT induce vomiting."
                ),
            }
        ],
    },
    {
        "health_problem": "Fever",
        "scientific_category": "Antipyretic / Analgesic",
        "medicines": [
            {
                "common_name": "Paracetamol (Acetaminophen)",
                "scientific_name": "N-(4-hydroxyphenyl)acetamide",
                "brand_names": ["Tylenol", "Panadol", "Biogesic"],
                "effects": "Reduces fever and mild-to-moderate pain without anti-inflammatory action.",
                "contraindications": [
                    "Severe liver disease",
                    "Alcohol dependence",
                    "Hypersensitivity to paracetamol",
                ],
                "global_equivalents": [
                    {
                        "country_region": "Philippines / Southeast Asia",
                        "plant": "Sambucus javanica (Elderberry / Sauco)",
                        "local_name": "Sauco",
                        "notes": "Bark decoction used traditionally for fever.",
                    },
                    {
                        "country_region": "Africa / Traditional medicine",
                        "plant": "Quassia amara",
                        "local_name": "Quassia",
                        "notes": "Bark infusion used as antipyretic.",
                    },
                    {
                        "country_region": "Central America / Mexico",
                        "plant": "Justicia pectoralis",
                        "local_name": "Tilo",
                        "notes": "Herbal tea for fever and headache.",
                    },
                ],
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Paracetamol-tablets.jpg/320px-Paracetamol-tablets.jpg",
                "first_aid_notes": (
                    "Overdose is a medical emergency. Symptoms may be delayed up to 24 hours. "
                    "Call poison control or emergency services immediately."
                ),
            }
        ],
    },
    {
        "health_problem": "Headache",
        "scientific_category": "Analgesic / NSAID",
        "medicines": [
            {
                "common_name": "Ibuprofen",
                "scientific_name": "(RS)-2-(4-(2-methylpropyl)phenyl)propanoic acid",
                "brand_names": ["Advil", "Motrin", "Nurofen"],
                "effects": (
                    "Reduces pain, fever, and inflammation by inhibiting COX-1 and COX-2 enzymes."
                ),
                "contraindications": [
                    "Active peptic ulcer",
                    "Severe renal/hepatic impairment",
                    "Last trimester of pregnancy",
                    "Hypersensitivity to NSAIDs / aspirin",
                ],
                "global_equivalents": [
                    {
                        "country_region": "Philippines / Southeast Asia",
                        "plant": "Lagundi (Vitex negundo)",
                        "local_name": "Lagundi",
                        "notes": (
                            "Approved by Philippine DOH as herbal analgesic/antipyretic."
                        ),
                    },
                    {
                        "country_region": "China / Traditional Chinese Medicine",
                        "plant": "Corydalis yanhusuo (Yan Hu Suo)",
                        "local_name": "延胡索 (Yánhúsuǒ)",
                        "notes": "Used for pain relief in TCM.",
                    },
                    {
                        "country_region": "Europe",
                        "plant": "Tanacetum parthenium (Feverfew)",
                        "local_name": "Feverfew",
                        "notes": "Used for migraine prevention.",
                    },
                ],
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Ibuprofen_200mg_tablets.jpg/320px-Ibuprofen_200mg_tablets.jpg",
                "first_aid_notes": (
                    "Overdose: induce vomiting only if conscious and advised by medical personnel. "
                    "Seek emergency care for large ingestion."
                ),
            }
        ],
    },
    {
        "health_problem": "Hypertension (High Blood Pressure)",
        "scientific_category": "Antihypertensive",
        "medicines": [
            {
                "common_name": "Amlodipine",
                "scientific_name": "3-ethyl 5-methyl (4RS)-2-[(2-aminoethoxy)methyl]-4-(2-chlorophenyl)-6-methyl-1,4-dihydropyridine-3,5-dicarboxylate",
                "brand_names": ["Norvasc", "Istin"],
                "effects": "Calcium channel blocker that relaxes blood vessels to lower blood pressure.",
                "contraindications": [
                    "Cardiogenic shock",
                    "Unstable angina",
                    "Severe aortic stenosis",
                    "Hypersensitivity to dihydropyridines",
                ],
                "global_equivalents": [
                    {
                        "country_region": "Philippines",
                        "plant": "Allium sativum (Garlic / Bawang)",
                        "local_name": "Bawang",
                        "notes": (
                            "Clinically studied mild antihypertensive; approved by Philippine DOH."
                        ),
                    },
                    {
                        "country_region": "India / Ayurveda",
                        "plant": "Rauwolfia serpentina",
                        "local_name": "Sarpagandha",
                        "notes": "Contains reserpine; historical antihypertensive.",
                    },
                    {
                        "country_region": "China / TCM",
                        "plant": "Uncaria rhynchophylla (Gou Teng)",
                        "local_name": "钩藤 (Gōuténg)",
                        "notes": "Used for hypertension and dizziness in TCM.",
                    },
                ],
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/Amlodipine_5mg_tablets.jpg/320px-Amlodipine_5mg_tablets.jpg",
                "first_aid_notes": (
                    "Hypertensive crisis (BP > 180/120): lie down, stay calm, loosen tight clothing, "
                    "call emergency services immediately. Do NOT abruptly skip doses."
                ),
            }
        ],
    },
    {
        "health_problem": "Infection (Bacterial)",
        "scientific_category": "Antibiotic",
        "medicines": [
            {
                "common_name": "Amoxicillin",
                "scientific_name": "(2S,5R,6R)-6-[[(2R)-2-amino-2-(4-hydroxyphenyl)acetyl]amino]-3,3-dimethyl-7-oxo-4-thia-1-azabicyclo[3.2.0]heptane-2-carboxylic acid",
                "brand_names": ["Amoxil", "Trimox"],
                "effects": "Broad-spectrum penicillin antibiotic inhibiting bacterial cell-wall synthesis.",
                "contraindications": [
                    "Penicillin or beta-lactam allergy",
                    "Infectious mononucleosis (risk of rash)",
                    "Severe renal impairment (dose adjustment required)",
                ],
                "global_equivalents": [
                    {
                        "country_region": "Philippines / Southeast Asia",
                        "plant": "Psidium guajava (Guava / Bayabas)",
                        "local_name": "Bayabas",
                        "notes": (
                            "Leaf extract shows antibacterial properties; approved by "
                            "Philippine DOH for wound/skin antiseptic use."
                        ),
                    },
                    {
                        "country_region": "Africa / Traditional medicine",
                        "plant": "Morinda lucida (Brimstone tree)",
                        "local_name": "Oruwo",
                        "notes": "Bark used for bacterial infections.",
                    },
                    {
                        "country_region": "Middle East / Mediterranean",
                        "plant": "Allium sativum (Garlic)",
                        "local_name": "Thoum (ثوم)",
                        "notes": "Raw garlic has broad-spectrum antibacterial activity.",
                    },
                ],
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Amoxicillin_capsules.jpg/320px-Amoxicillin_capsules.jpg",
                "first_aid_notes": (
                    "Allergic reaction (anaphylaxis): administer epinephrine (EpiPen) if available, "
                    "call emergency services, lay patient flat with legs elevated."
                ),
            }
        ],
    },
    {
        "health_problem": "Nausea / Vomiting",
        "scientific_category": "Antiemetic",
        "medicines": [
            {
                "common_name": "Metoclopramide",
                "scientific_name": "4-amino-5-chloro-N-[2-(diethylamino)ethyl]-2-methoxybenzamide",
                "brand_names": ["Reglan", "Plasil", "Maxolon"],
                "effects": (
                    "Dopamine receptor antagonist; increases gastric motility and prevents nausea/vomiting."
                ),
                "contraindications": [
                    "GI obstruction or perforation",
                    "Phaeochromocytoma",
                    "History of tardive dyskinesia",
                    "Epilepsy",
                ],
                "global_equivalents": [
                    {
                        "country_region": "Philippines / Southeast Asia",
                        "plant": "Zingiber officinale (Ginger / Luya)",
                        "local_name": "Luya",
                        "notes": (
                            "Clinically proven antiemetic; approved by Philippine DOH."
                        ),
                    },
                    {
                        "country_region": "India / Ayurveda",
                        "plant": "Elettaria cardamomum (Cardamom)",
                        "local_name": "Elaichi",
                        "notes": "Chewing cardamom seeds relieves nausea.",
                    },
                    {
                        "country_region": "Europe / North America",
                        "plant": "Mentha × piperita (Peppermint)",
                        "local_name": "Peppermint",
                        "notes": "Peppermint tea or oil capsules reduce nausea.",
                    },
                ],
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/Ginger_roots.jpg/320px-Ginger_roots.jpg",
                "first_aid_notes": (
                    "Prevent aspiration: position patient sitting or on their side. "
                    "Keep hydrated with small sips of clear fluid. Seek care if vomiting persists > 24 h."
                ),
            }
        ],
    },
    {
        "health_problem": "Wound / Skin Infection",
        "scientific_category": "Topical Antiseptic",
        "medicines": [
            {
                "common_name": "Povidone-Iodine",
                "scientific_name": "1-Ethenyl-2-pyrrolidinone – molecular iodine complex",
                "brand_names": ["Betadine"],
                "effects": "Broad-spectrum topical antiseptic that kills bacteria, fungi, and viruses.",
                "contraindications": [
                    "Iodine hypersensitivity",
                    "Thyroid disorders (large wounds/prolonged use)",
                    "Premature neonates",
                    "Avoid in eyes/ears",
                ],
                "global_equivalents": [
                    {
                        "country_region": "Philippines / Southeast Asia",
                        "plant": "Psidium guajava (Guava / Bayabas)",
                        "local_name": "Bayabas",
                        "notes": (
                            "Leaf decoction used to wash wounds; Philippine DOH approved herbal."
                        ),
                    },
                    {
                        "country_region": "Africa",
                        "plant": "Aloe vera",
                        "local_name": "Aloe",
                        "notes": "Gel applied to minor burns, cuts, and skin infections.",
                    },
                    {
                        "country_region": "Europe / Global",
                        "plant": "Calendula officinalis (Pot marigold)",
                        "local_name": "Calendula",
                        "notes": "Anti-inflammatory wound-healing cream/ointment.",
                    },
                ],
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7f/Betadine_solution_bottle.jpg/320px-Betadine_solution_bottle.jpg",
                "first_aid_notes": (
                    "Clean wound with running water, apply antiseptic, cover with sterile dressing. "
                    "Seek care for deep, heavily contaminated, or bite wounds."
                ),
            }
        ],
    },
]


def get_catalog_sorted_by_health_problem(catalog: list[dict]) -> list[dict]:
    """Return the medicine catalog sorted alphabetically by health problem name."""
    return sorted(catalog, key=lambda entry: entry["health_problem"].lower())


# ---------------------------------------------------------------------------
# Helper: build a plain-text catalog summary for prompt injection
# ---------------------------------------------------------------------------
def _build_catalog_text(catalog: list[dict]) -> str:
    lines = []
    for entry in catalog:
        lines.append(f"\n=== {entry['health_problem']} ({entry['scientific_category']}) ===")
        for med in entry["medicines"]:
            lines.append(f"  Medicine : {med['common_name']}")
            lines.append(f"  Sci. name: {med['scientific_name']}")
            lines.append(f"  Brands   : {', '.join(med['brand_names'])}")
            lines.append(f"  Effects  : {med['effects']}")
            lines.append(f"  Contra   : {'; '.join(med['contraindications'])}")
            lines.append("  Global equivalents:")
            for eq in med["global_equivalents"]:
                lines.append(
                    f"    [{eq['country_region']}] {eq['plant']} ({eq['local_name']}): {eq['notes']}"
                )
            lines.append(f"  First aid: {med['first_aid_notes']}")
            lines.append(f"  Image URL: {med['image_url']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# System instructions
# ---------------------------------------------------------------------------
CATALOG_SYSTEM_INSTRUCTION = (
    "You are MediGuide, a compassionate and knowledgeable medical information assistant. "
    "Your goals are:\n"
    "1. Provide accurate, alphabetically ordered information about medicines, their scientific "
    "names, effects, contraindications, and global plant/herbal equivalents from different "
    "countries and regions.\n"
    "2. Offer calm, clear first-aid guidance during emergencies, reminding users to contact "
    "emergency services when needed.\n"
    "3. Detect signs of fear, anxiety, or distress in the user's language, and respond with "
    "empathy and a soothing tone before proceeding with clinical information.\n"
    "4. Conduct a gentle, structured symptom interview: ask one question at a time, listen "
    "carefully, summarize what you have learned, and only offer information when you have "
    "enough context.\n"
    "5. When the user shares patient health records (text, documents, or images), analyze them "
    "carefully and summarize key findings, abnormal values, and recommended follow-up actions.\n"
    "\n"
    "IMPORTANT DISCLAIMER: Always remind the user that your information is educational, not a "
    "substitute for professional medical advice. Encourage consultation with a qualified "
    "healthcare provider for diagnosis and treatment.\n"
    "\n"
    "Below is the medicine catalog you may reference:\n"
    "{catalog}"
)

EMOTIONAL_SUPPORT_PROMPT = (
    "Before answering any medical question, briefly acknowledge the patient's emotional state "
    "if they seem anxious, scared, or distressed. Use a warm, reassuring tone. Then gently "
    "guide them through the relevant information or interview questions."
)


class UnitTests(absltest.TestCase):
    # ------------------------------------------------------------------
    # 1. Print sorted catalog
    # ------------------------------------------------------------------
    def test_catalog_sorted_alphabetically(self):
        """Verifies that get_catalog_sorted_by_health_problem returns entries in A-Z order."""
        # [START catalog_sorted]
        sorted_catalog = get_catalog_sorted_by_health_problem(MEDICINE_CATALOG)
        for entry in sorted_catalog:
            print(
                f"{entry['health_problem']:40s} | "
                f"{entry['scientific_category']:30s} | "
                f"{entry['medicines'][0]['common_name']}"
            )
        # [END catalog_sorted]
        names = [e["health_problem"].lower() for e in sorted_catalog]
        self.assertEqual(names, sorted(names))

    # ------------------------------------------------------------------
    # 2. AI catalog lookup (text-only)
    # ------------------------------------------------------------------
    def test_medicine_catalog_lookup(self):
        # [START medicine_catalog_lookup]
        import google.generativeai as genai

        catalog_text = _build_catalog_text(get_catalog_sorted_by_health_problem(MEDICINE_CATALOG))
        system_prompt = CATALOG_SYSTEM_INSTRUCTION.format(catalog=catalog_text)

        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            system_instruction=system_prompt,
        )
        response = model.generate_content(
            "What medicine is used for fever? "
            "List its scientific name, effects, contraindications, and any plant-based "
            "equivalents used in Southeast Asia."
        )
        print(response.text)
        # [END medicine_catalog_lookup]

    # ------------------------------------------------------------------
    # 3. AI first-aid / emergency diagnosis
    # ------------------------------------------------------------------
    def test_emergency_first_aid_diagnosis(self):
        # [START emergency_first_aid]
        import google.generativeai as genai

        catalog_text = _build_catalog_text(get_catalog_sorted_by_health_problem(MEDICINE_CATALOG))
        system_prompt = CATALOG_SYSTEM_INSTRUCTION.format(catalog=catalog_text)

        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            system_instruction=system_prompt,
        )
        chat = model.start_chat()

        # Simulate an emergency query
        emergency_query = (
            "EMERGENCY: My child accidentally swallowed several paracetamol tablets about "
            "30 minutes ago. What should I do right now?"
        )
        response = chat.send_message(emergency_query)
        print("=== EMERGENCY RESPONSE ===")
        print(response.text)
        # [END emergency_first_aid]

    # ------------------------------------------------------------------
    # 4. Emotional-state-aware patient interaction
    # ------------------------------------------------------------------
    def test_emotional_state_aware_interaction(self):
        # [START emotional_state_aware]
        import google.generativeai as genai

        catalog_text = _build_catalog_text(get_catalog_sorted_by_health_problem(MEDICINE_CATALOG))
        system_prompt = (
            CATALOG_SYSTEM_INSTRUCTION.format(catalog=catalog_text)
            + "\n\n"
            + EMOTIONAL_SUPPORT_PROMPT
        )

        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            system_instruction=system_prompt,
        )
        chat = model.start_chat()

        # Step 1 – patient expresses fear/distress
        response1 = chat.send_message(
            "I'm terrified. My heart is pounding and I don't know what is wrong with me. "
            "Please help me."
        )
        print("=== STEP 1: Emotional acknowledgement ===")
        print(response1.text)

        # Step 2 – symptom interview
        response2 = chat.send_message(
            "I've had a very bad headache since yesterday, and I feel dizzy whenever I stand up."
        )
        print("\n=== STEP 2: Symptom interview ===")
        print(response2.text)

        # Step 3 – follow-up
        response3 = chat.send_message(
            "No, I haven't taken any medication. I do have high blood pressure but I ran out "
            "of my pills three days ago."
        )
        print("\n=== STEP 3: Personalized guidance ===")
        print(response3.text)
        # [END emotional_state_aware]

    # ------------------------------------------------------------------
    # 5. Structured symptom interview
    # ------------------------------------------------------------------
    def test_symptom_interview(self):
        # [START symptom_interview]
        import google.generativeai as genai

        interview_instruction = (
            "You are a compassionate medical intake assistant. "
            "Conduct a structured symptom interview by asking ONE focused question at a time. "
            "After gathering enough information (at least 4-5 responses), provide a summary of "
            "the likely health concern and recommend the appropriate next steps. "
            "Always maintain a calm, non-alarmist tone."
        )

        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            system_instruction=interview_instruction,
        )
        chat = model.start_chat()

        conversation = [
            "I haven't been feeling well.",
            "It started two days ago. Mostly in my stomach area.",
            "It's a dull aching pain, about 5 out of 10.",
            "Yes, I also have some nausea and lost my appetite.",
            "No fever, but I feel a bit bloated.",
        ]

        for turn in conversation:
            response = chat.send_message(turn)
            print(f"Patient : {turn}")
            print(f"MediGuide: {response.text}\n")
        # [END symptom_interview]

    # ------------------------------------------------------------------
    # 6. Patient health record analysis
    # ------------------------------------------------------------------
    def test_health_record_analysis(self):
        # [START health_record_analysis]
        import google.generativeai as genai

        record_analyst_instruction = (
            "You are a clinical data analyst assistant. "
            "When given a patient health record, you will:\n"
            "1. Summarize the key findings concisely.\n"
            "2. Highlight any abnormal values or concerning patterns.\n"
            "3. Suggest appropriate follow-up actions or specialist referrals.\n"
            "4. Remind the user that all findings must be confirmed by a licensed physician.\n"
            "Maintain a professional yet empathetic tone."
        )

        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            system_instruction=record_analyst_instruction,
        )

        # Simulated patient health record (text)
        patient_record = """
        Patient: Maria Santos, 58 F
        Date: 2024-03-15

        Chief Complaint: Persistent headache, dizziness, fatigue for 1 week.

        Vital Signs:
          Blood Pressure : 168/102 mmHg  [HIGH]
          Heart Rate     : 88 bpm
          Temperature    : 36.8 °C
          SpO2           : 97%

        Lab Results:
          Fasting Blood Glucose : 7.8 mmol/L  [HIGH – Normal < 6.1]
          Total Cholesterol     : 6.4 mmol/L  [HIGH – Normal < 5.2]
          LDL Cholesterol       : 4.1 mmol/L  [HIGH – Normal < 3.4]
          HDL Cholesterol       : 1.1 mmol/L  [Borderline low]
          Serum Creatinine      : 98 µmol/L   [Normal]
          eGFR                  : 72 mL/min   [Mildly reduced]

        Current Medications: Amlodipine 5 mg once daily (reported 3-day gap in intake)

        Allergies: None known.

        Notes: Patient concerned about side effects of blood-pressure medications.
        """

        response = model.generate_content(
            f"Please analyse the following patient health record:\n\n{patient_record}"
        )
        print(response.text)
        # [END health_record_analysis]

    # ------------------------------------------------------------------
    # 7. Multimodal: Identify medicine from image
    # ------------------------------------------------------------------
    def test_medicine_image_identification(self):
        # [START medicine_image_identification]
        import google.generativeai as genai
        import PIL.Image

        # Use a local test image if available, otherwise skip gracefully.
        organ_image_path = media / "organ.jpg"
        if not organ_image_path.exists():
            self.skipTest("Test image not found; skipping multimodal test.")

        model = genai.GenerativeModel("gemini-1.5-flash")

        # In a real deployment you would supply an actual medicine/plant image.
        # Here we use the sample media image as a placeholder.
        image = PIL.Image.open(organ_image_path)
        response = model.generate_content(
            [
                "Pretend this is a photograph of a medicinal plant or tablet. "
                "Describe what you see, identify the possible medicine or plant, "
                "state its common and scientific name, primary uses, and any safety warnings.",
                image,
            ]
        )
        print(response.text)
        # [END medicine_image_identification]


if __name__ == "__main__":
    absltest.main()

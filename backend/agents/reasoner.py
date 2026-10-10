"""
Clinical Reasoning & NLP Agent for MedMap.
Understands natural language healthcare queries (including conversational phrasing,
Hinglish, and medical descriptions), extracts clinical presentation, performs differential
diagnosis, formulates 3 to 5 genuine diagnostic triage questions, and refines
hospital recommendations based on the patient's answers.
"""
import json
import logging
import re
from typing import Dict, List, Any, Optional

from config import settings
from schemas.hospital import DiagnosticQuestion, ClinicalAnalysis

logger = logging.getLogger(__name__)

# ── Clinical Knowledge Base & Symptom Ontologies ──────────────────────────────

CLINICAL_SYMPTOM_DOMAINS = {
    "acute_abdomen": {
        "keywords": [
            "appendectomy", "appendix", "abdominal", "abdomen", "stomach pain", "belly",
            "pet dard", "pet me dard", "right lower", "navel", "umbilicus", "vomiting", "ulti",
            "nausea", "chubhan", "aithan", "loose motion", "peritonitis", "gallbladder", "pancreatitis",
            "stomach ache", "cramp", "rigid abdomen", "bloating", "gas pain", "swelling in stomach"
        ],
        "default_complaint": "Acute Abdominal Pain / Suspected Surgical Abdomen",
        "primary_conditions": [
            "Acute Appendicitis (High Risk if localized to RLQ)",
            "Acute Gastroenteritis / Enteritis",
            "Cholecystitis / Gallbladder Colic",
            "Renal / Ureteric Calculus (Kidney Stone)",
            "Perforated Peptic Ulcer / Peritonitis"
        ],
        "urgency": "CRITICAL_EMERGENCY",
        "required_capabilities": ["surgery", "emergency_24h"],
        "required_equipment": ["Operation Theatre (OT)", "Ultrasound Abdomen / CT", "IV Fluids & Analgesics", "Laparoscopy Unit"],
        "red_flags": [
            "Rebound tenderness / board-like rigidity",
            "Pain migration from navel to right lower abdomen (McBurney's sign)",
            "High fever with persistent vomiting",
            "Inability to pass flatus or stool with abdominal distension"
        ],
        "guidance": "Keep patient strictly fasting (NPO - Nil Per Os) immediately in case emergency surgery is needed. Do not give strong laxatives or heating pads.",
        "questions": [
            {
                "id": "q_pain_migration",
                "question": "Has the pain moved or localized to your lower right abdomen, or does it worsen when coughing or walking?",
                "options": [
                    "Yes, shifted to lower right and hurts when walking",
                    "No, severe pain all over the stomach",
                    "Upper stomach near ribs / heartburn",
                    "Lower pelvic area / groin"
                ],
                "rationale": "Identifies classic McBurney's point migration indicative of acute appendicitis vs generalized dyspepsia.",
                "category": "symptom_localization",
            },
            {
                "id": "q_fever_vomiting",
                "question": "Are you experiencing a fever, nausea, or recurrent vomiting?",
                "options": [
                    "Both fever (>100°F) and vomiting",
                    "Vomiting only, no fever",
                    "Mild nausea only",
                    "Neither fever nor vomiting"
                ],
                "rationale": "High fever with persistent vomiting indicates active intra-abdominal inflammation or impending perforation.",
                "category": "systemic_severity",
            },
            {
                "id": "q_food_tolerance",
                "question": "When did you last eat or drink, and are you able to keep fluids down?",
                "options": [
                    "Cannot keep anything down (vomiting everything)",
                    "Ate 4-6 hours ago, feeling nauseous",
                    "Can drink fluids without vomiting",
                    "Normal appetite despite pain"
                ],
                "rationale": "Critical for surgical anesthesia readiness and assessing dehydration / electrolyte shock risk.",
                "category": "surgical_prerequisite",
            },
            {
                "id": "q_urinary_bowel",
                "question": "Have you noticed any severe burning while urinating, blood in urine, or missed periods (if female)?",
                "options": [
                    "Burning urination or dark urine",
                    "Severe diarrhea or blood in stool",
                    "Missed period / possibility of pregnancy",
                    "None of these symptoms"
                ],
                "rationale": "Differentiates appendicitis from urinary tract infection, kidney stones, or ectopic pregnancy.",
                "category": "differential_rule_out",
            },
        ],
    },
    "chest_pain_cardiac": {
        "keywords": [
            "chest pain", "heart", "cardiac", "angina", "attack", "chhati me dard",
            "chest pressure", "left arm", "jaw pain", "palpitation", "sweat", "paseena",
            "heavy chest", "crushing pain", "heartburn", "ghabrahat", "breathless", "bp"
        ],
        "default_complaint": "Acute Chest Pain / Suspected Cardiac Event",
        "primary_conditions": [
            "Acute Coronary Syndrome / Myocardial Infarction (Heart Attack)",
            "Unstable Angina Pectoris",
            "Aortic Dissection / Severe Hypertensive Crisis",
            "Gastroesophageal Reflux (GERD) / Costochondritis"
        ],
        "urgency": "CRITICAL_EMERGENCY",
        "required_capabilities": ["icu", "cardiac_surgery", "emergency_24h"],
        "required_equipment": ["12-Lead ECG", "Troponin Biomarker Testing", "Cardiac Monitor / Defibrillator", "Oxygen Support", "Cath Lab (Preferred)"],
        "red_flags": [
            "Radiation of crushing pain to left shoulder, arm, neck, or jaw",
            "Profuse cold sweating (diaphoresis)",
            "Severe shortness of breath or dizziness/syncope",
            "History of diabetes, hypertension, or previous stent/bypass"
        ],
        "guidance": "Immediately call for an ambulance. Keep the patient resting upright. If no allergy or active bleeding, chew 300mg soluble Aspirin immediately while en route.",
        "questions": [
            {
                "id": "q_pain_radiation",
                "question": "Does the chest pain or heaviness radiate into your left arm, neck, shoulder, or jaw?",
                "options": [
                    "Yes, radiating down left arm or jaw",
                    "Radiates to upper back between shoulder blades",
                    "Stays centered in middle of chest",
                    "Sharp pain that changes when pressing ribs"
                ],
                "rationale": "Radiation to the left arm or jaw carries a high likelihood ratio for acute myocardial ischemia.",
                "category": "symptom_localization",
            },
            {
                "id": "q_cold_sweats",
                "question": "Are you having cold sweating, sudden extreme dizziness, or nausea with the chest discomfort?",
                "options": [
                    "Yes, breaking into cold sweats and dizzy",
                    "Mild nausea only",
                    "Shortness of breath without sweating",
                    "No sweating or dizziness"
                ],
                "rationale": "Diaphoresis and autonomic symptoms signify high-grade sympathetic cardiac distress.",
                "category": "systemic_severity",
            },
            {
                "id": "q_pain_character",
                "question": "How does the pain feel, and does resting or deep breathing change it?",
                "options": [
                    "Crushing heavy pressure / tight band around chest",
                    "Burning sensation behind breastbone",
                    "Sharp stabbing pain worse with deep breaths",
                    "Comes and goes with exertion"
                ],
                "rationale": "Distinguishes ischemic pressure from pleuritic, musculoskeletal, or acid reflux causes.",
                "category": "differential_rule_out",
            },
            {
                "id": "q_cardiac_history",
                "question": "Do you have a personal or family history of high blood pressure, diabetes, smoking, or heart issues?",
                "options": [
                    "Yes, diabetic or high BP",
                    "Previous heart stent / bypass surgery",
                    "Smoker / family heart history",
                    "No known medical conditions"
                ],
                "rationale": "Significantly alters baseline pre-test probability for coronary artery thrombosis.",
                "category": "risk_stratification",
            },
        ],
    },
    "respiratory_distress": {
        "keywords": [
            "breathless", "shortness of breath", "breathing", "saans", "asthma", "wheezing",
            "suffocation", "oxygen", "spo2", "coughing blood", "blue lips", "gasping",
            "hafnan", "chhati jam", "pneumonia", "copd"
        ],
        "default_complaint": "Acute Respiratory Distress / Hypoxemia",
        "primary_conditions": [
            "Acute Exacerbation of Asthma / COPD",
            "Severe Pneumonia / Lower Respiratory Tract Infection",
            "Pulmonary Edema / Congestive Heart Failure",
            "Pulmonary Embolism / Acute Bronchospasm"
        ],
        "urgency": "CRITICAL_EMERGENCY",
        "required_capabilities": ["icu", "emergency_24h"],
        "required_equipment": ["High-Flow Oxygen Pipeline", "Mechanical Ventilator / BiPAP", "Nebulization Unit", "Pulse Oximeter", "Chest X-Ray"],
        "red_flags": [
            "Inability to speak in full sentences",
            "Bluish discoloration of lips or nail beds (cyanosis)",
            "SpO2 dropping below 90%",
            "Stridor or audible tracheal wheezing"
        ],
        "guidance": "Seat patient upright. Administer prescribed rescue inhaler / nebulizer if available. Keep windows open for air circulation while en route to oxygen-equipped center.",
        "questions": [
            {
                "id": "q_speech_breathing",
                "question": "Can you or the patient speak in full sentences without needing to gasp for air?",
                "options": [
                    "Can only speak 1-2 words at a time (Severe)",
                    "Can speak short sentences with effort",
                    "Breathing is fast but can speak normally",
                    "Breathing difficulty only when lying down flat"
                ],
                "rationale": "Assesses impending respiratory muscle exhaustion and mechanical failure.",
                "category": "acuity_check",
            },
            {
                "id": "q_fever_phlegm",
                "question": "Is the breathlessness accompanied by high fever, cough with thick sputum, or chest rattling?",
                "options": [
                    "High fever with yellow/green or blood-tinged sputum",
                    "Dry continuous hacking cough",
                    "Audible whistling / wheezing sound",
                    "No cough or fever, sudden onset"
                ],
                "rationale": "Differentiates bacterial consolidation (pneumonia) from reactive airway disease or cardiac asthma.",
                "category": "differential_rule_out",
            },
            {
                "id": "q_oxygen_levels",
                "question": "If you have a pulse oximeter, what is the current SpO2 level, or are lips turning bluish?",
                "options": [
                    "SpO2 below 90% or lips look bluish / pale",
                    "SpO2 between 90% and 94%",
                    "SpO2 above 95%",
                    "No pulse oximeter available"
                ],
                "rationale": "Quantifies hypoxemia to trigger immediate BiPAP or invasive mechanical ventilation protocol.",
                "category": "systemic_severity",
            },
            {
                "id": "q_swelling_legs",
                "question": "Is there noticeable swelling in both feet/ankles or sudden weight gain recently?",
                "options": [
                    "Yes, noticeable leg/feet swelling (edema)",
                    "Swelling in only one leg with calf pain",
                    "No swelling anywhere",
                    "Not sure"
                ],
                "rationale": "Screens for congestive heart failure with fluid overload versus deep vein thrombosis with pulmonary embolism.",
                "category": "differential_rule_out",
            },
        ],
    },
    "trauma_accident": {
        "keywords": [
            "accident", "trauma", "fracture", "bleeding", "injury", "fall", "bike accident",
            "haddi toot", "khoon beh", "head injury", "concussion", "wound", "deep cut",
            "broken leg", "bone", "crush", "road traffic"
        ],
        "default_complaint": "Acute Trauma / Musculoskeletal Injury / Active Hemorrhage",
        "primary_conditions": [
            "Traumatic Bone Fracture / Dislocation",
            "Internal Hemorrhage / Blunt Abdominal Trauma",
            "Closed Head Injury / Traumatic Brain Injury",
            "Soft Tissue Laceration with Vascular Injury"
        ],
        "urgency": "CRITICAL_EMERGENCY",
        "required_capabilities": ["trauma", "surgery", "blood_bank", "emergency_24h"],
        "required_equipment": ["Emergency Trauma OT", "Digital X-Ray / CT Scanner", "Blood Storage / Transfusion Unit", "Orthopedic Splinting / External Fixation"],
        "red_flags": [
            "Active spurting or uncontrolled bleeding",
            "Loss of consciousness, vomiting, or memory loss after head impact",
            "Visible bone protruding through skin (compound fracture)",
            "Cold, pale, or pulseless limb below injury site"
        ],
        "guidance": "Apply firm direct pressure with clean cloth over bleeding wounds. Immobilize suspected fracture limb. Do not move patient if neck or spinal injury is suspected.",
        "questions": [
            {
                "id": "q_consciousness_head",
                "question": "Was there any loss of consciousness, confusion, vomiting, or bleeding from ear/nose?",
                "options": [
                    "Yes, lost consciousness or vomited after hit",
                    "Dazed/confused but did not black out",
                    "Bleeding from scalp but fully awake",
                    "No head injury occurred"
                ],
                "rationale": "Identifies intracranial hemorrhage / concussion requiring urgent non-contrast head CT.",
                "category": "acuity_check",
            },
            {
                "id": "q_active_bleeding",
                "question": "Is there severe or continuous bleeding that is soaking through bandages?",
                "options": [
                    "Spurting / heavy bleeding not stopping with pressure",
                    "Bleeding slowed down with firm cloth pressure",
                    "Minor scraping / controlled bleeding",
                    "No external bleeding, only severe pain"
                ],
                "rationale": "Flags hemorrhagic shock and necessity for on-site blood transfusion and surgical ligation.",
                "category": "systemic_severity",
            },
            {
                "id": "q_bone_deformity",
                "question": "Can the patient move the injured limb, bear weight, or is there an abnormal bend/protruding bone?",
                "options": [
                    "Bone is visible or limb is bent at unnatural angle",
                    "Completely unable to bear weight or move limb",
                    "Can move fingers/toes with severe swelling and pain",
                    "Only skin bruises, joints move freely"
                ],
                "rationale": "Identifies open compound fracture requiring emergency debridement and orthopedic reduction.",
                "category": "surgical_prerequisite",
            },
            {
                "id": "q_abdominal_impact",
                "question": "Did the patient suffer any direct impact to the stomach, chest, or pelvis?",
                "options": [
                    "Yes, hit handlebars / steering wheel directly on stomach",
                    "Crush injury to chest or pelvis",
                    "Only hit arms / legs",
                    "No torso impact"
                ],
                "rationale": "Screens for occult splenic rupture or liver laceration causing internal hypovolemic shock.",
                "category": "red_flag_screening",
            },
        ],
    },
    "pediatric_fever": {
        "keywords": [
            "child", "baby", "bachha", "infant", "pediatric", "high fever", "tez bukhar",
            "not feeding", "lethargic", "shivering", "convulsion", "seizure", "vomiting baby",
            "doodh nahi pee raha", "crying continuously", "rash"
        ],
        "default_complaint": "Pediatric Acute Febrile Illness / Potential Neonatal Sepsis",
        "primary_conditions": [
            "Acute Febrile Seizure / Pediatric Infection",
            "Severe Dengue / Malaria / Enteric Sepsis",
            "Acute Bronchiolitis / Pneumonia",
            "Severe Dehydration secondary to Gastroenteritis"
        ],
        "urgency": "CRITICAL_EMERGENCY",
        "required_capabilities": ["nicu", "icu", "emergency_24h"],
        "required_equipment": ["Pediatric / Neonatal ICU (NICU/PICU)", "Pediatrician on call", "Infant Warmer / Phototherapy", "IV Pediatric Infusion Pump"],
        "red_flags": [
            "Extreme drowsiness, limpness, or difficulty waking up",
            "Refusal to feed or nurse for over 8-12 hours",
            "Continuous high fever with rapid grunting breaths",
            "Jerking movements / convulsions or petechial purple rash"
        ],
        "guidance": "Do not wrap baby in heavy blankets. Sponge forehead and body with room-temperature tap water (not cold). Seek immediate medical evaluation by a pediatrician.",
        "questions": [
            {
                "id": "q_alertness_feeding",
                "question": "Is the child alert and able to drink liquids, or are they unusually limp and sleepy?",
                "options": [
                    "Very limp, drowsy, refusing all feeds/milk",
                    "Irritable and crying continuously, hard to calm",
                    "Drinking small amounts but vomits often",
                    "Alert and playful between fever spikes"
                ],
                "rationale": "Altered sensorium or refusal to feed is the #1 WHO danger sign in pediatric triage.",
                "category": "acuity_check",
            },
            {
                "id": "q_fever_duration",
                "question": "How high is the fever and how many days has it been present?",
                "options": [
                    "Over 103°F (39.4°C) or lasting > 3 days",
                    "Between 100°F and 102°F for 1-2 days",
                    "Fever started just today",
                    "Not measured with thermometer but feels burning hot"
                ],
                "rationale": "High persistent fever increases risk of febrile seizures, severe dengue, or bacteremia.",
                "category": "systemic_severity",
            },
            {
                "id": "q_breathing_effort",
                "question": "Is the child breathing rapidly, or can you see ribs sucking inward (chest indrawing)?",
                "options": [
                    "Yes, chest sucking inward and rapid breathing",
                    "Fast breathing with noisy wheezing or grunting",
                    "Normal breathing with nasal congestion only",
                    "Breathing seems fine"
                ],
                "rationale": "Chest indrawing is a hallmark sign of severe pediatric lower respiratory tract infection.",
                "category": "red_flag_screening",
            },
            {
                "id": "q_skin_rash",
                "question": "Have you noticed any reddish/purple spots on skin or bleeding from gums/nose?",
                "options": [
                    "Purple tiny spots that do not fade when pressed (petechiae)",
                    "Pink blotchy rash all over body",
                    "No rash anywhere",
                    "Dry lips and sunken eyes (severe dehydration)"
                ],
                "rationale": "Petechial rash signals meningococcemia or severe dengue thrombocytopenia.",
                "category": "differential_rule_out",
            },
        ],
    },
    "dialysis_renal": {
        "keywords": [
            "dialysis", "kidney", "renal", "creatinine", "swelling", "edema", "sujan",
            "peshab band", "no urine", "hemodialysis", "fistula", "nephrology", "urea"
        ],
        "default_complaint": "End-Stage Renal Disease / Uremic Crisis / Missed Dialysis",
        "primary_conditions": [
            "Acute Uremic Encephalopathy / Fluid Overload",
            "Hyperkalemia secondary to Missed Hemodialysis",
            "AV Fistula Thrombosis or Infection",
            "Acute Kidney Injury (AKI) superimposed on CKD"
        ],
        "urgency": "URGENT",
        "required_capabilities": ["dialysis", "icu", "emergency_24h"],
        "required_equipment": ["Hemodialysis Machines", "Reverse Osmosis (RO) Water Plant", "Nephrologist / Dialysis Technician", "ECG & Potassium Correction Kit"],
        "red_flags": [
            "Extreme breathlessness when lying flat (pulmonary edema)",
            "Confusion, drowsiness, or twitching (uremia)",
            "Irregular heartbeat / skipped beats (hyperkalemia risk)",
            "Loss of thrill or bruit in dialysis AV fistula"
        ],
        "guidance": "Strictly restrict fluid intake. Avoid high-potassium foods (bananas, coconut water, citrus fruits). Proceed immediately to an operational dialysis center.",
        "questions": [
            {
                "id": "q_missed_sessions",
                "question": "How many days has it been since the last hemodialysis session was completed?",
                "options": [
                    "Missed 2 or more scheduled sessions (Overdue > 4 days)",
                    "Missed 1 scheduled session (Overdue 1-2 days)",
                    "Had dialysis yesterday but feeling breathless/sick",
                    "Not on regular dialysis yet (New kidney diagnosis)"
                ],
                "rationale": "Quantifies severity of fluid overload and lethal potassium accumulation.",
                "category": "acuity_check",
            },
            {
                "id": "q_breathlessness_orthopnea",
                "question": "Is the patient breathless when lying flat in bed, or having cough with pink frothy sputum?",
                "options": [
                    "Cannot lie flat at all, must sit up to breathe",
                    "Breathless on mild walking",
                    "Swelling in legs and face but breathing is okay",
                    "No breathlessness"
                ],
                "rationale": "Orthopnea indicates acute fluid extravasation into pulmonary alveoli requiring emergent ultrafiltration.",
                "category": "systemic_severity",
            },
            {
                "id": "q_urine_output",
                "question": "How much urine has the patient passed in the past 24 hours?",
                "options": [
                    "Zero or negligible drops of urine (Anuria)",
                    "Noticeably decreased / dark colored urine",
                    "Normal quantity of urine",
                    "Undergoing regular hemodialysis with minimal urine baseline"
                ],
                "rationale": "Differentiates acute oliguric kidney injury from established dialysis status.",
                "category": "differential_rule_out",
            },
            {
                "id": "q_fistula_status",
                "question": "If the patient has an AV fistula in the arm, is the usual vibration/buzzing (thrill) still felt?",
                "options": [
                    "Buzzing/vibration stopped or arm is swollen and painful",
                    "Buzzing feels normal in fistula",
                    "Using a temporary neck catheter (Jugular / Permacath)",
                    "No fistula or catheter in place"
                ],
                "rationale": "Detects acute vascular access thrombosis requiring urgent vascular declotting.",
                "category": "surgical_prerequisite",
            },
        ],
    },
    "neurological_stroke": {
        "keywords": [
            "stroke", "paralysis", "face drooping", "speech", "slurred", "weakness one side",
            "aadha sharir", "sunn", "loss of balance", "thunderclap headache", "chakkar",
            "fainting", "seizure", "epilepsy", "mirgi", "brain"
        ],
        "default_complaint": "Acute Stroke Symptoms / Neurological Emergency",
        "primary_conditions": [
            "Acute Ischemic Stroke (Golden Window < 4.5 hours for Thrombolysis)",
            "Intracerebral / Subarachnoid Hemorrhage",
            "Transient Ischemic Attack (TIA)",
            "Status Epilepticus / Complex Partial Seizure"
        ],
        "urgency": "CRITICAL_EMERGENCY",
        "required_capabilities": ["icu", "neurosurgery", "emergency_24h"],
        "required_equipment": ["Non-contrast Brain CT Scanner", "tPA Thrombolysis Medication", "Stroke ICU / Neurologist", "Neuro-surgical OT"],
        "red_flags": [
            "FAST: Face drooping, Arm drift, Slurred speech",
            "Sudden severe headache ('worst headache of life')",
            "Onset of symptoms within the past 4.5 hours (Time is Brain)",
            "Unconsciousness or continuous repetitive seizures"
        ],
        "guidance": "Note exact time symptoms started. Do not give food, water, or blood thinners (Aspirin) until CT scan rules out brain hemorrhage. Rush to a CT-equipped stroke hospital.",
        "questions": [
            {
                "id": "q_stroke_onset_time",
                "question": "Exactly when were the symptoms first noticed or when was the patient last seen normal?",
                "options": [
                    "Less than 3 hours ago (Within Golden Window for IV clot buster)",
                    "Between 3 and 4.5 hours ago",
                    "Between 4.5 and 24 hours ago",
                    "Over 24 hours ago or gradual progression"
                ],
                "rationale": "Determines eligibility for life-saving IV rtPA thrombolysis (approved within 4.5 hours).",
                "category": "acuity_check",
            },
            {
                "id": "q_fast_symptoms",
                "question": "Which of these specific signs are present right now?",
                "options": [
                    "One side of face drooping and cannot smile evenly",
                    "One arm drifts down when holding both arms out",
                    "Words are slurred or cannot speak coherently",
                    "All three (Face, Arm, and Speech affected)"
                ],
                "rationale": "Validates the Cincinnati Prehospital Stroke Scale with >88% diagnostic sensitivity.",
                "category": "symptom_localization",
            },
            {
                "id": "q_headache_severity",
                "question": "Is there a sudden, explosive headache ('thunderclap') unlike anything experienced before?",
                "options": [
                    "Yes, sudden agonizing headache that peaked in seconds",
                    "Moderate headache with nausea",
                    "Dull ache / heaviness only",
                    "No headache at all"
                ],
                "rationale": "High sensitivity marker for aneurysmal subarachnoid hemorrhage.",
                "category": "differential_rule_out",
            },
            {
                "id": "q_blood_sugar_history",
                "question": "Is the patient diabetic, and has blood sugar been checked recently?",
                "options": [
                    "Diabetic, blood sugar checked and is normal",
                    "Diabetic, blood sugar not checked (could be hypoglycemia)",
                    "Not diabetic",
                    "History of previous stroke / mini-stroke"
                ],
                "rationale": "Severe hypoglycemia is the most common mimic of acute ischemic stroke.",
                "category": "risk_stratification",
            },
        ],
    },
}

# General Fallback Questions for other health complaints
GENERAL_QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": "q_gen_duration",
        "question": "How long have you been experiencing these symptoms, and have they suddenly worsened?",
        "options": [
            "Started suddenly within the last few hours",
            "Started 1-2 days ago and getting steadily worse",
            "Persistent for over a week",
            "Chronic recurring problem"
        ],
        "rationale": "Establishes acute versus subacute trajectory.",
        "category": "acuity_check",
    },
    {
        "id": "q_gen_severity",
        "question": "On a scale of 1 to 10, how intense is the pain or discomfort right now?",
        "options": [
            "Severe (8-10): Unbearable, cannot perform basic tasks",
            "Moderate (5-7): Significant distress but manageable",
            "Mild (1-4): Discomfort, able to carry out daily tasks",
            "No pain, experiencing other symptoms (fever, rash, fatigue)"
        ],
        "rationale": "Standardized subjective pain and distress indexing.",
        "category": "systemic_severity",
    },
    {
        "id": "q_gen_red_flags",
        "question": "Are you experiencing any warning signs such as high fever, uncontrollable vomiting, bleeding, or dizziness?",
        "options": [
            "High fever with severe chills or weakness",
            "Dizziness, feeling faint, or cold sweats",
            "Continuous vomiting or inability to keep water down",
            "None of these warning signs"
        ],
        "rationale": "Screens for systemic decompensation and sepsis.",
        "category": "red_flag_screening",
    },
    {
        "id": "q_gen_specialty_need",
        "question": "Do you need urgent diagnostic scans (such as Ultrasound, X-Ray, CT) or an immediate specialist consultation?",
        "options": [
            "Need emergency doctor and diagnostic imaging immediately",
            "Need specific surgical specialist consultation",
            "Need outpatient medical checkup and prescription",
            "Need ICU / admission bed immediately"
        ],
        "rationale": "Directly filters hospital infrastructure and equipment prerequisites.",
        "category": "surgical_prerequisite",
    },
]


def detect_clinical_domain(text: str) -> Optional[str]:
    """Detect matching clinical domain from natural language query or complaints."""
    q_lower = text.lower()
    
    # Priority check for specific acute conditions
    best_domain = None
    max_matches = 0

    for domain_key, domain_info in CLINICAL_SYMPTOM_DOMAINS.items():
        matches = sum(1 for kw in domain_info["keywords"] if kw in q_lower)
        if matches > max_matches:
            max_matches = matches
            best_domain = domain_key

    return best_domain if max_matches > 0 else None


def analyze_natural_language_request(
    query: str,
    diagnostic_answers: Optional[Dict[str, str]] = None
) -> ClinicalAnalysis:
    """
    Main NLP & Clinical Reasoning engine:
    1. Analyzes the user's natural language problem.
    2. Identifies clinical symptoms, suspected conditions, red flags, and acuity.
    3. Formulates 3 to 5 genuine diagnostic questions.
    4. If user answers are provided, refines the diagnosis, urgency, and capability requirements.
    """
    q_lower = query.lower()
    domain_key = detect_clinical_domain(query)
    answers = diagnostic_answers or {}

    if domain_key and domain_key in CLINICAL_SYMPTOM_DOMAINS:
        domain = CLINICAL_SYMPTOM_DOMAINS[domain_key]
        primary_complaint = domain["default_complaint"]
        differential = list(domain["primary_conditions"])
        urgency = domain["urgency"]
        required_caps = list(domain["required_capabilities"])
        required_eq = list(domain["required_equipment"])
        red_flags = list(domain["red_flags"])
        guidance = domain["guidance"]
        raw_questions = domain["questions"]
    else:
        primary_complaint = "General Medical Evaluation & Clinical Triage"
        differential = [
            "Acute Medical Illness requiring differential diagnostic workup",
            "Subacute or Chronic condition exacerbation",
            "Infectious or Inflammatory pathology"
        ]
        urgency = "URGENT" if any(w in q_lower for w in ["emergency", "urgent", "tez", "pain", "dard", "fever", "bukhar"]) else "ROUTINE"
        required_caps = ["emergency_24h"] if urgency == "URGENT" else []
        required_eq = ["Diagnostic Pathology Lab", "Digital X-Ray / Ultrasound", "Resident Medical Officer (RMO)"]
        red_flags = ["Persistent high fever > 102°F", "Severe unmanageable pain", "Intractable vomiting or inability to tolerate fluids"]
        guidance = "Seek prompt evaluation at a verified medical center. Avoid self-medicating with over-the-counter pain relievers before a doctor examines you."
        raw_questions = GENERAL_QUESTIONS

    # Format questions
    diagnostic_questions = [
        DiagnosticQuestion(
            id=q["id"],
            question=q["question"],
            options=q["options"],
            rationale=q.get("rationale"),
            category=q.get("category", "clinical_triage")
        )
        for q in raw_questions
    ]

    # Refine diagnosis and urgency based on user answers
    confirmed_dx = None
    clarification_points = []

    if answers:
        logger.info(f"Refining clinical reasoning with {len(answers)} user answers: {answers}")

        # Check domain-specific answer clues
        if domain_key == "acute_abdomen":
            q1_ans = answers.get("q_pain_migration", "").lower()
            q2_ans = answers.get("q_fever_vomiting", "").lower()
            q3_ans = answers.get("q_food_tolerance", "").lower()

            if "lower right" in q1_ans:
                confirmed_dx = "Acute Appendicitis (Localized to Right Iliac Fossa / McBurney's Point)"
                differential.insert(0, confirmed_dx)
                required_caps.extend(["surgery", "emergency_24h"])
                required_eq.extend(["Laparoscopic OT Unit", "General Surgeon on Duty", "Anesthesiologist"])
                clarification_points.append("Patient confirmed classic localized right lower quadrant pain.")

            if "fever" in q2_ans and "vomiting" in q2_ans:
                urgency = "CRITICAL_EMERGENCY"
                clarification_points.append("High systemic inflammatory markers indicated by concurrent fever and emesis.")

            if "cannot keep anything down" in q3_ans:
                clarification_points.append("Severe oral intolerance — requires immediate IV hydration and fasting protocol for general anesthesia.")

        elif domain_key == "chest_pain_cardiac":
            q1_ans = answers.get("q_pain_radiation", "").lower()
            q2_ans = answers.get("q_cold_sweats", "").lower()

            if "left arm" in q1_ans or "jaw" in q1_ans:
                confirmed_dx = "Acute Coronary Syndrome (High Suspicion of STEMI / NSTEMI)"
                differential.insert(0, confirmed_dx)
                urgency = "CRITICAL_EMERGENCY"
                required_caps.extend(["icu", "cardiac_surgery", "emergency_24h"])
                clarification_points.append("Radiation to left upper limb / jaw confirmed; activates critical cardiac protocol.")

            if "cold sweat" in q2_ans or "dizzy" in q2_ans:
                clarification_points.append("Diaphoresis confirmed — high risk of cardiogenic instability.")

        elif domain_key == "respiratory_distress":
            q1_ans = answers.get("q_speech_breathing", "").lower()
            q3_ans = answers.get("q_oxygen_levels", "").lower()

            if "1-2 words" in q1_ans:
                urgency = "CRITICAL_EMERGENCY"
                clarification_points.append("Severe respiratory exhaustion: patient unable to speak in sentences.")

            if "below 90%" in q3_ans or "bluish" in q3_ans:
                urgency = "CRITICAL_EMERGENCY"
                confirmed_dx = "Acute Severe Hypoxemic Respiratory Failure"
                differential.insert(0, confirmed_dx)
                required_caps.extend(["icu", "emergency_24h"])
                required_eq.extend(["Mechanical Ventilator", "High-Flow Oxygen Pipeline"])
                clarification_points.append("Severe hypoxemia confirmed (SpO2 < 90%). Direct routing to ventilator-capable ICU required.")

        elif domain_key == "trauma_accident":
            q1_ans = answers.get("q_consciousness_head", "").lower()
            q2_ans = answers.get("q_active_bleeding", "").lower()
            q3_ans = answers.get("q_bone_deformity", "").lower()

            if "lost consciousness" in q1_ans:
                confirmed_dx = "Traumatic Brain Injury / Concussion with Polytrauma"
                differential.insert(0, confirmed_dx)
                urgency = "CRITICAL_EMERGENCY"
                required_caps.extend(["trauma", "neurosurgery", "emergency_24h"])
                required_eq.append("Immediate Non-Contrast Head CT")
                clarification_points.append("Loss of consciousness confirmed: mandatory non-contrast brain CT.")

            if "bone is visible" in q3_ans or "unnatural angle" in q3_ans:
                confirmed_dx = "Compound Open Fracture / Major Orthopedic Disruption"
                differential.insert(0, confirmed_dx)
                urgency = "CRITICAL_EMERGENCY"
                required_caps.extend(["trauma", "surgery", "blood_bank"])
                clarification_points.append("Compound bone deformity confirmed: emergency surgical debridement and orthopedic reduction required within 6 hours.")

        elif domain_key == "dialysis_renal":
            q1_ans = answers.get("q_missed_sessions", "").lower()
            q2_ans = answers.get("q_breathlessness_orthopnea", "").lower()

            if "missed 2" in q1_ans or "cannot lie flat" in q2_ans:
                confirmed_dx = "Critical Uremic Hypervolemia / Impending Pulmonary Edema"
                differential.insert(0, confirmed_dx)
                urgency = "CRITICAL_EMERGENCY"
                required_caps.extend(["dialysis", "icu", "emergency_24h"])
                clarification_points.append("Severe volume overload and orthopnea confirmed: emergent ultrafiltration hemodialysis indicated.")

        elif domain_key == "neurological_stroke":
            q1_ans = answers.get("q_stroke_onset_time", "").lower()
            q2_ans = answers.get("q_fast_symptoms", "").lower()

            if "less than 3 hours" in q1_ans or "3 and 4.5" in q1_ans:
                confirmed_dx = "Acute Ischemic Stroke within Thrombolytic Golden Window"
                differential.insert(0, confirmed_dx)
                urgency = "CRITICAL_EMERGENCY"
                required_caps.extend(["icu", "neurosurgery", "emergency_24h"])
                required_eq.extend(["Emergency Brain CT", "rtPA Clot Buster"])
                clarification_points.append("Patient is within the 4.5-hour golden window: prioritized for immediate CT and IV thrombolysis.")

        # General answer checks
        for q_id, ans_val in answers.items():
            if "severe" in ans_val.lower() or "unbearable" in ans_val.lower():
                urgency = "CRITICAL_EMERGENCY"
                clarification_points.append(f"High severity reported for question '{q_id}'.")

    # Determine urgency color badge
    urgency_color = "red" if urgency == "CRITICAL_EMERGENCY" else ("amber" if urgency == "URGENT" else "emerald")

    clarification_summary = None
    if clarification_points:
        clarification_summary = f"Refined with patient inputs: {'; '.join(clarification_points)}"

    return ClinicalAnalysis(
        primary_complaint=primary_complaint,
        urgency_tier=urgency,
        urgency_color=urgency_color,
        differential_diagnosis=differential[:4],
        confirmed_diagnosis=confirmed_dx,
        red_flags=red_flags,
        required_capabilities=list(dict.fromkeys(required_caps)),
        required_equipment=list(dict.fromkeys(required_eq)),
        patient_guidance=guidance,
        clarification_summary=clarification_summary,
        questions=diagnostic_questions,
    )


def evaluate_hospital_clinical_fitness(
    hospital_data: Dict[str, Any],
    clinical_analysis: ClinicalAnalysis
) -> tuple[float, List[str]]:
    """
    Evaluates how accurately a hospital record satisfies the specific clinical
    requirements extracted from the user's natural language presentation.
    Returns (clinical_bonus, match_reasons).
    """
    bonus = 0.0
    reasons = []

    func_caps = hospital_data.get("functional_capabilities") or {}
    caps = hospital_data.get("capabilities") or {}
    equipment = hospital_data.get("equipment_list") or []
    specialties = hospital_data.get("staff_specialties") or []
    equip_str = " ".join(str(e) for e in equipment).lower()
    spec_str = " ".join(str(s) for s in specialties).lower()

    # 1. Check required capabilities
    for cap in clinical_analysis.required_capabilities:
        fc = func_caps.get(cap, {})
        if isinstance(fc, dict) and fc.get("status") == "VERIFIED_FUNCTIONAL":
            bonus += 20.0
            reasons.append(f"Verified {cap.upper()} capability: {fc.get('evidence', 'On duty & equipped')[:65]}")
        elif caps.get(cap) is True:
            bonus += 10.0
            reasons.append(f"Listed {cap.upper()} facility")
        elif isinstance(fc, dict) and fc.get("status") == "PHANTOM_CAPABILITY":
            bonus -= 30.0
            reasons.append(f"FLAGGED: Phantom {cap.upper()} claim (-30 pts)")

    # 2. Check diagnostic equipment matches
    for eq in clinical_analysis.required_equipment:
        eq_low = eq.lower()
        if any(token in equip_str for token in ["ot", "laparo", "ventilator", "ultrasound", "ct", "x-ray", "dialysis"]):
            bonus += 8.0
            reasons.append(f"Equipped with key diagnostic/treatment infrastructure ({eq})")
            break

    # 3. Check specialist staff matches
    if "surgery" in clinical_analysis.required_capabilities:
        if any(s in spec_str for s in ["general surgery", "surgeon", "laparoscop"]):
            bonus += 15.0
            reasons.append("General / Laparoscopic surgeon on roster")
    if "cardiac" in clinical_analysis.required_capabilities:
        if any(s in spec_str for s in ["cardiolog", "cardiac"]):
            bonus += 15.0
            reasons.append("Cardiology department available")

    # 4. Critical emergency readiness
    if clinical_analysis.urgency_tier == "CRITICAL_EMERGENCY":
        ec = func_caps.get("emergency_24h", {})
        if isinstance(ec, dict) and ec.get("status") == "VERIFIED_FUNCTIONAL":
            bonus += 15.0
            reasons.append("24/7 Casualty & Emergency admission verified")
        elif caps.get("emergency_24h") is not True:
            bonus -= 20.0
            reasons.append("WARNING: Lacks verified 24/7 casualty for emergency")

    # Format reasons (top 3)
    if not reasons:
        reasons.append("General medical care available")

    return bonus, reasons[:3]

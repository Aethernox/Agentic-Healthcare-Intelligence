# Databricks notebook source
# MAGIC %md
# MAGIC # MedMap — Step 4: Trust Scoring Pipeline
# MAGIC Apply contradiction rules + Tavily verification to all 10,000 hospital records

# COMMAND ----------

import mlflow
import json
import asyncio
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf
from pyspark.sql.types import IntegerType, StringType, ArrayType

spark = SparkSession.builder.getOrCreate()

TAVILY_API_KEY = dbutils.secrets.get(scope="medmap", key="tavily_api_key")
TAVILY_TRIGGER_THRESHOLD = 50

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Contradiction Rules Engine

# COMMAND ----------

CONTRADICTION_RULES = [
    ("surgery_no_anesthesiologist", "Claims Surgery but no Anesthesiologist listed", 30),
    ("icu_no_ventilators", "Claims ICU but no ventilators mentioned", 25),
    ("emergency_no_night_staff", "Claims 24/7 Emergency but no night staff", 20),
    ("nicu_no_equipment", "Claims NICU but no neonatal equipment listed", 25),
    ("oncology_no_oncologist", "Claims Oncology but no oncologist in staff", 30),
    ("nabh_no_date", "Claims NABH accreditation but no date", 15),
    ("cardiac_no_cath_lab", "Claims Cardiac Surgery but no cath lab", 25),
    ("dialysis_no_nephrologist", "Claims Dialysis but no nephrologist", 20),
]


def compute_trust_score(record_json: str) -> dict:
    try:
        record = json.loads(record_json)
        score = 100
        flags = []

        caps = record.get("capabilities", {}) or {}
        staff = [s.lower() for s in record.get("staff_specialties", []) or []]
        equipment = [e.lower() for e in record.get("equipment_list", []) or []]

        def has_staff(*kws): return any(any(kw in s for kw in kws) for s in staff)
        def has_equip(*kws): return any(any(kw in e for kw in kws) for e in equipment)

        checks = [
            ("surgery_no_anesthesiologist", caps.get("surgery") and not has_staff("anesthesiolog", "anaesthesiolog"), 30),
            ("icu_no_ventilators", caps.get("icu") and not has_equip("ventilator") and not record.get("ventilator_count"), 25),
            ("emergency_no_night_staff", caps.get("emergency_24h") and not has_staff("night", "24/7", "resident"), 20),
            ("nicu_no_equipment", caps.get("nicu") and not has_equip("incubator", "nicu"), 25),
            ("oncology_no_oncologist", caps.get("oncology") and not has_staff("oncolog"), 30),
            ("nabh_no_date", record.get("accreditation") and not record.get("accreditation_date"), 15),
            ("cardiac_no_cath_lab", caps.get("cardiac_surgery") and not has_equip("cath lab", "cardiac icu"), 25),
            ("dialysis_no_nephrologist", caps.get("dialysis") and not has_staff("nephrolog"), 20),
        ]

        for rule_id, triggered, penalty in checks:
            if triggered:
                score -= penalty
                label = next((r[1] for r in CONTRADICTION_RULES if r[0] == rule_id), rule_id)
                flags.append(label)

        # Completeness bonus
        if record.get("accreditation") and record.get("accreditation_date"):
            score = min(score + 5, 100)
        if (record.get("extraction_confidence") or 0) >= 0.9:
            score = min(score + 3, 100)

        return {
            "trust_score": max(0, min(score, 100)),
            "trust_flags": flags,
            "needs_tavily": score < TAVILY_TRIGGER_THRESHOLD,
        }

    except Exception as e:
        return {"trust_score": 0, "trust_flags": [f"Error: {str(e)}"], "needs_tavily": True}


# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Apply Trust Scoring to All Records

# COMMAND ----------

with mlflow.start_run(run_name="trust-scoring-pipeline"):
    mlflow.log_param("trigger_threshold", TAVILY_TRIGGER_THRESHOLD)
    mlflow.log_param("rules_count", len(CONTRADICTION_RULES))

    extracted_pdf = spark.table("medmap.extracted.hospitals_json").toPandas()

    trust_results = []
    for _, row in extracted_pdf.iterrows():
        result = compute_trust_score(row["extracted_json"])
        trust_results.append({
            "record_id": row["record_id"],
            **result,
            "trust_flags_str": json.dumps(result["trust_flags"]),
        })

    trust_pdf = pd.DataFrame(trust_results)

    high_trust = (trust_pdf["trust_score"] >= 75).sum()
    medium_trust = ((trust_pdf["trust_score"] >= 40) & (trust_pdf["trust_score"] < 75)).sum()
    low_trust = (trust_pdf["trust_score"] < 40).sum()
    tavily_triggers = trust_pdf["needs_tavily"].sum()

    mlflow.log_metric("high_trust_count", int(high_trust))
    mlflow.log_metric("medium_trust_count", int(medium_trust))
    mlflow.log_metric("low_trust_count", int(low_trust))
    mlflow.log_metric("tavily_triggered", int(tavily_triggers))

    print(f"Trust Distribution:")
    print(f"  🟢 High (75-100): {high_trust:,}")
    print(f"  🟡 Medium (40-74): {medium_trust:,}")
    print(f"  🔴 Low (0-39): {low_trust:,}")
    print(f"  🌐 Tavily triggers: {tavily_triggers:,}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Tavily Verification for Low-Trust Records

# COMMAND ----------

from tavily import TavilyClient
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

low_trust_records = trust_pdf[trust_pdf["needs_tavily"] == True].head(50)  # Start with 50 for demo

verified_results = []
for _, row in low_trust_records.iterrows():
    record = json.loads(extracted_pdf[extracted_pdf["record_id"] == row["record_id"]].iloc[0]["extracted_json"])
    name = record.get("name", "Unknown")
    city = record.get("city", "")

    try:
        search_result = tavily_client.search(
            query=f"{name} {city} hospital medical facility India",
            search_depth="basic",
            max_results=3,
        )

        content = " ".join(r.get("content", "") for r in search_result.get("results", []))
        if any(kw in content.lower() for kw in ["hospital", "clinic", "medical", "health"]):
            adjustment = +10
            summary = f"Web search confirms {name} is an active medical facility."
        else:
            adjustment = -5
            summary = f"Limited web evidence found for {name}."

        verified_results.append({
            "record_id": row["record_id"],
            "tavily_verified": True,
            "tavily_adjustment": adjustment,
            "tavily_summary": summary,
        })

    except Exception as e:
        verified_results.append({
            "record_id": row["record_id"],
            "tavily_verified": False,
            "tavily_adjustment": 0,
            "tavily_summary": f"Verification failed: {str(e)[:100]}",
        })

print(f"✅ Tavily verified {len(verified_results)} low-trust records")

# COMMAND ----------

# Save final trust scores
trust_sdf = spark.createDataFrame(trust_pdf.drop(columns=["trust_flags"]))
trust_sdf.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("medmap.scored.hospital_trust")

print("✅ Trust scores written to medmap.scored.hospital_trust")
display(spark.table("medmap.scored.hospital_trust").orderBy(col("trust_score")).limit(10))

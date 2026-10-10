# Databricks notebook source
# MAGIC %md
# MAGIC # MedMap — Step 2: LLM Extraction via Claude API
# MAGIC Extract structured hospital data from raw text records using Claude claude-3-5-sonnet-20241022

# COMMAND ----------

import mlflow
import json
import asyncio
import pandas as pd
from anthropic import Anthropic
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from pyspark.sql.types import StringType

spark = SparkSession.builder.getOrCreate()

# COMMAND ----------

# Set your Anthropic API key
import os
ANTHROPIC_API_KEY = dbutils.secrets.get(scope="medmap", key="anthropic_api_key")
client = Anthropic(api_key=ANTHROPIC_API_KEY)

# COMMAND ----------

mlflow.set_experiment("/medmap/extraction-pipeline")

EXTRACTION_PROMPT = """Extract structured medical facility information from this Indian hospital record.
Return ONLY valid JSON with these fields (null if not found):

{
  "name": "string",
  "city": "string",
  "district": "string",
  "state": "string",
  "pin_code": "string",
  "bed_count": integer_or_null,
  "icu_beds": integer_or_null,
  "ventilator_count": integer_or_null,
  "staff_specialties": ["array", "of", "specialties"],
  "equipment_list": ["array", "of", "equipment"],
  "accreditation": "NABH/NABL/JCI or null",
  "accreditation_date": "date string or null",
  "capabilities": {
    "icu": true_false_null,
    "surgery": true_false_null,
    "emergency_24h": true_false_null,
    "dialysis": true_false_null,
    "nicu": true_false_null,
    "oncology": true_false_null,
    "trauma": true_false_null,
    "blood_bank": true_false_null,
    "cardiac_surgery": true_false_null
  },
  "extraction_confidence": 0.0_to_1.0
}

Record: {record}"""


def extract_single_record(raw_text: str, record_id: int) -> str:
    """Extract a single hospital record via Claude API."""
    try:
        with mlflow.start_run(nested=True, run_name=f"extract_record_{record_id}"):
            mlflow.log_param("record_id", record_id)
            mlflow.log_param("text_length", len(raw_text))

            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(record=raw_text[:3000])
                }]
            )

            result_text = response.content[0].text.strip()
            if "```" in result_text:
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            result_text = result_text.strip()

            parsed = json.loads(result_text)
            mlflow.log_metric("extraction_confidence", parsed.get("extraction_confidence", 0))
            mlflow.log_param("status", "success")

            return json.dumps(parsed)

    except Exception as e:
        mlflow.log_param("status", "failed")
        mlflow.log_param("error", str(e)[:200])
        return json.dumps({"error": str(e), "name": f"Record {record_id}"})


# COMMAND ----------

# MAGIC %md
# MAGIC ## Run Extraction (Batched with Spark UDF)

# COMMAND ----------

extract_udf = udf(lambda text, rid: extract_single_record(text, rid), StringType())

with mlflow.start_run(run_name="full-extraction-pipeline"):
    mlflow.log_param("model", "claude-3-5-sonnet-20241022")
    mlflow.log_param("dataset", "VF_Hackathon_India_Large")

    raw_df = spark.table("medmap.raw.hospitals")
    total = raw_df.count()
    mlflow.log_param("total_records", total)

    # Process in batches to respect API rate limits
    BATCH_SIZE = 100
    results = []

    raw_pdf = raw_df.select("record_id", "raw_text").toPandas()

    for i in range(0, min(len(raw_pdf), 10000), BATCH_SIZE):
        batch = raw_pdf.iloc[i:i + BATCH_SIZE]
        batch_results = []
        for _, row in batch.iterrows():
            extracted = extract_single_record(row["raw_text"], row["record_id"])
            batch_results.append({"record_id": row["record_id"], "extracted_json": extracted})
        results.extend(batch_results)
        print(f"Processed {min(i + BATCH_SIZE, len(raw_pdf))}/{len(raw_pdf)} records")

    extracted_pdf = pd.DataFrame(results)
    extracted_sdf = spark.createDataFrame(extracted_pdf)

    extracted_sdf.write.format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .saveAsTable("medmap.extracted.hospitals_json")

    mlflow.log_metric("records_extracted", len(results))
    print(f"✅ Extraction complete: {len(results):,} records")

# COMMAND ----------

display(spark.table("medmap.extracted.hospitals_json").limit(5))

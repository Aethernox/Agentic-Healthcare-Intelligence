# Databricks notebook source
# MAGIC %md
# MAGIC # MedMap — Step 1: Data Ingestion
# MAGIC Load and clean the VF Hackathon dataset into Unity Catalog

# COMMAND ----------

import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, trim, regexp_extract, monotonically_increasing_id

spark = SparkSession.builder.getOrCreate()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Load Raw Excel

# COMMAND ----------

# Upload the file to DBFS first:
# dbutils.fs.cp("file:/path/to/VF_Hackathon_Dataset_India_Large.xlsx", "dbfs:/FileStore/medmap/raw/hospitals.xlsx")

RAW_FILE_PATH = "dbfs:/FileStore/medmap/raw/hospitals.xlsx"

pdf = pd.read_excel(f"/dbfs{RAW_FILE_PATH.replace('dbfs:', '')}", engine="openpyxl")
print(f"Loaded {len(pdf):,} records, columns: {list(pdf.columns)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Normalize Columns

# COMMAND ----------

COLUMN_MAP = {
    "Hospital Name": "name",
    "Facility Name": "name",
    "State": "state",
    "District": "district",
    "City": "city",
    "PIN Code": "pin_code",
    "Pincode": "pin_code",
    "Total Beds": "bed_count",
    "Beds": "bed_count",
    "Description": "raw_text",
    "Facilities": "raw_text",
}

pdf = pdf.rename(columns={c: COLUMN_MAP.get(c, c.lower().replace(" ", "_")) for c in pdf.columns})

# Build raw_text from all columns if not present
if "raw_text" not in pdf.columns:
    non_text_cols = []
    pdf["raw_text"] = pdf.apply(
        lambda row: " | ".join(f"{col}: {val}" for col, val in row.items() if pd.notna(val)),
        axis=1,
    )

pdf = pdf.dropna(subset=["raw_text"])
pdf["record_id"] = range(1, len(pdf) + 1)
print(f"After cleaning: {len(pdf):,} records")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Write to Unity Catalog (Delta)

# COMMAND ----------

sdf = spark.createDataFrame(pdf)
sdf = sdf.withColumn("name", trim(col("name"))) if "name" in sdf.columns else sdf

sdf.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("medmap.raw.hospitals")

print(f"✅ Written {sdf.count():,} records to medmap.raw.hospitals")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Preview

# COMMAND ----------

display(spark.table("medmap.raw.hospitals").limit(10))

"""
LLM-powered extraction agent that converts unstructured hospital records
into structured HospitalExtracted objects using OpenAI.
"""
import json
import logging
from typing import Optional

from openai import AsyncOpenAI

from schemas.hospital import HospitalExtracted, Capabilities
from config import settings

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """You are a medical data extraction specialist. Extract structured information from the following Indian hospital record.

Return a valid JSON object with these fields (use null if information is not found):
{
  "name": "Hospital full name",
  "city": "City name",
  "district": "District name",
  "state": "State name",
  "pin_code": "6-digit PIN code",
  "bed_count": <integer or null>,
  "icu_beds": <integer or null>,
  "ventilator_count": <integer or null>,
  "staff_specialties": ["list", "of", "medical", "specialties"],
  "equipment_list": ["list", "of", "equipment"],
  "accreditation": "NABH/NABL/JCI or null",
  "accreditation_date": "date string or null",
  "capabilities": {
    "icu": <true/false/null>,
    "surgery": <true/false/null>,
    "emergency_24h": <true/false/null>,
    "dialysis": <true/false/null>,
    "nicu": <true/false/null>,
    "oncology": <true/false/null>,
    "trauma": <true/false/null>,
    "blood_bank": <true/false/null>,
    "cardiac_surgery": <true/false/null>,
    "neurosurgery": <true/false/null>,
    "burn_unit": <true/false/null>,
    "psychiatric": <true/false/null>
  },
  "extraction_confidence": <0.0-1.0 float based on how clear the record is>
}

Rules:
- Only mark a capability as true if explicitly stated or strongly implied
- Use null (not false) when information is absent or ambiguous
- Extract staff specialties verbatim from the record
- extraction_confidence should reflect data completeness (1.0 = all fields clear)

Hospital Record:
{record}

Return ONLY valid JSON. No explanations."""


async def extract_hospital_record(
    raw_text: str,
    record_id: Optional[int] = None,
    client: Optional[AsyncOpenAI] = None,
) -> HospitalExtracted:
    """
    Extract structured data from a raw hospital record using GPT-4o.
    Falls back to empty structure if extraction fails.
    """
    if client is None:
        client = AsyncOpenAI(api_key=settings.openai_api_key)

    try:
        prompt = EXTRACTION_PROMPT.format(record=raw_text[:3000])

        response = await client.chat.completions.create(
            model="gpt-4o",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )

        raw_json = response.choices[0].message.content.strip()

        data = json.loads(raw_json)

        capabilities_data = data.pop("capabilities", {})
        capabilities = Capabilities(**{k: v for k, v in capabilities_data.items() if v is not None})

        hospital = HospitalExtracted(
            **{k: v for k, v in data.items() if v is not None},
            capabilities=capabilities,
            raw_text=raw_text,
            extraction_source=f"Record ID {record_id}: {raw_text[:200]}…" if record_id else raw_text[:200],
        )

        logger.info(f"Extracted record {record_id}: {hospital.name} (confidence: {hospital.extraction_confidence})")
        return hospital

    except Exception as e:
        logger.error(f"Extraction failed for record {record_id}: {e}")
        return HospitalExtracted(
            name=f"Record {record_id}" if record_id else "Unknown",
            raw_text=raw_text,
            extraction_confidence=0.0,
        )


async def batch_extract(
    records: list[dict],
    client: Optional[AsyncOpenAI] = None,
    concurrency: int = 5,
) -> list[HospitalExtracted]:
    """
    Batch-extract multiple records with controlled concurrency.
    """
    import asyncio
    from asyncio import Semaphore

    if client is None:
        client = AsyncOpenAI(api_key=settings.openai_api_key)

    semaphore = Semaphore(concurrency)

    async def extract_with_limit(record):
        async with semaphore:
            return await extract_hospital_record(
                raw_text=record.get("raw_text", ""),
                record_id=record.get("id"),
                client=client,
            )

    tasks = [extract_with_limit(r) for r in records]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    extracted = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Record {i} extraction failed: {result}")
        else:
            extracted.append(result)

    return extracted

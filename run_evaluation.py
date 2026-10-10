import json
import requests
from pathlib import Path

# Configuration
INPUT_FILE = Path(
    r"D:\Software Projects\Kinetics Hackathon ( Team - Pragati )\participant_eval_kit\samples\ps03_practice_probes.jsonl"
)

OUTPUT_FILE = Path(
    r"D:\Software Projects\Kinetics Hackathon ( Team - Pragati )\participant_eval_kit\samples\outputs.jsonl"
)

FAILURE_FILE = OUTPUT_FILE.parent / "evaluation_failures.jsonl"

API_URL = "http://localhost:8000/solve"

successful = 0
failed = 0

# Validate input file
if not INPUT_FILE.exists():
    raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

# Load input probes
with INPUT_FILE.open("r", encoding="utf-8") as file:
    probes = [
        json.loads(line)
        for line in file
        if line.strip()
    ]

print(f"Loaded {len(probes)} probes.\n")

# Process probes and write one JSON object per line
with OUTPUT_FILE.open("w", encoding="utf-8") as output_file, \
     FAILURE_FILE.open("w", encoding="utf-8") as failure_file:

    for index, probe in enumerate(probes, start=1):
        probe_id = probe.get("probe_id", f"probe_{index}")

        # Support both wrapped probes and direct API payloads
        payload = probe.get("input", probe)

        print(
            f"[{index}/{len(probes)}] Running {probe_id}...",
            end=" ",
            flush=True
        )

        try:
            response = requests.post(
                API_URL,
                json=payload,
                timeout=300
            )

            response.raise_for_status()
            output = response.json()

            if not isinstance(output, dict):
                raise ValueError(
                    "API response must be a JSON object."
                )

            # Preserve the input probe ID for evaluation
            output["probe_id"] = probe_id

            # Write JSONL: exactly one JSON object per line
            output_file.write(
                json.dumps(output, ensure_ascii=False) + "\n"
            )
            output_file.flush()

            successful += 1
            print("OK")

        except (requests.RequestException, ValueError) as exc:
            failure_record = {
                "probe_id": probe_id,
                "error": str(exc)
            }

            failure_file.write(
                json.dumps(failure_record, ensure_ascii=False) + "\n"
            )
            failure_file.flush()

            failed += 1
            print(f"FAILED: {exc}")

print("\n========== Evaluation Run Summary ==========")
print(f"Total probes: {len(probes)}")
print(f"Successful:   {successful}")
print(f"Failed:       {failed}")
print(f"Output file:  {OUTPUT_FILE.resolve()}")

if failed:
    print(f"Failure details: {FAILURE_FILE.resolve()}")
else:
    FAILURE_FILE.unlink(missing_ok=True)
    print("All probes completed successfully.")
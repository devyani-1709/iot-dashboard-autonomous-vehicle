from ultralytics import YOLO
import csv
import os
from datetime import datetime

# === 1️⃣ Path to your dataset YAML ===
DATA_YAML = r"C:\IoT_Software\datasets\JAAD\data.yaml"

# === 2️⃣ Load YOLOv11n model ===
model = YOLO("yolo11n.pt")

# === 3️⃣ Run validation on your dataset ===
print("\n--- Starting validation... ---")
res = model.val(data=DATA_YAML, imgsz=640, split="val", save_json=True)
print("--- Validation complete. ---")

# === 4️⃣ Extract and save key metrics (Final Correct Version) ===
metrics = {}
try:
    # Get the results dictionary
    d = res.results_dict
    
    # Use the EXACT keys we found from the debug output
    metrics['mAP50'] = d['metrics/mAP50(B)']
    metrics['mAP50-95'] = d['metrics/mAP50-95(B)']
    metrics['precision'] = d['metrics/precision(B)']
    metrics['recall'] = d['metrics/recall(B)']
    
    # Calculate F1 score
    p = metrics['precision']
    r = metrics['recall']
    if (p + r) > 0:
        metrics['F1'] = (2 * p * r) / (p + r)
    else:
        metrics['F1'] = 0.0

    print("\n--- ✅ Success! Extracted metrics: ---")
    print(f"mAP@0.5 (mAP50):    {metrics['mAP50']}")
    print(f"mAP@0.5:0.95 (map): {metrics['mAP50-95']}")
    print(f"Precision:          {metrics['precision']}")
    print(f"Recall:             {metrics['recall']}")
    print(f"F1 Score:           {metrics['F1']}")

except Exception as e:
    print(f"\n⚠️ CRITICAL: Unable to parse metrics from results_dict: {e}")
    print("This may be because validation failed. Check output above for errors.")
    print("Available keys were:", res.results_dict.keys())


# === 5️⃣ Save metrics to CSV with timestamp ===
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
out_csv = f"yolo11n_eval_summary_{timestamp}.csv"

with open(out_csv, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["metric", "value"])
    for k, v in metrics.items():
        writer.writerow([k, v])

print(f"\n✅ Metrics saved to: {out_csv}")

# === 6️⃣ Identify latest validation run folder ===
runs_base = "runs/detect/val"
run_dir = None
if os.path.exists(runs_base):
    # Sort by modification time to find the newest folder
    runs = sorted([os.path.join(runs_base, d) for d in os.listdir(runs_base) if os.path.isdir(os.path.join(runs_base, d))], key=os.path.getmtime)
    if runs:
        run_dir = runs[-1] # Get the last one

if run_dir:
    print(f"📊 Find PR curves, confusion matrix, etc. in:\n   {run_dir}")
else:
    print("⚠️ Validation run images not found — check runs/detect/val/ for saved plots.")
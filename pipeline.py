from vision_agent import detect_snag
from analysis_agent import analyze
from report_agent import generate_report
from email_agent import generate_email
from learning_agent import store_feedback
from draw_boxes import filter_predictions, merge_boxes, draw_merged_box

import os
import cv2

def get_bbox_from_user():

    print("\nEnter bounding box coordinates:")

    x1 = int(input("Top-left X: "))
    y1 = int(input("Top-left Y: "))
    x2 = int(input("Bottom-right X: "))
    y2 = int(input("Bottom-right Y: "))

    return {
        "x": int((x1 + x2) / 2),
        "y": int((y1 + y2) / 2),
        "width": abs(x2 - x1),
        "height": abs(y2 - y1)
    }


# ---------------------------
# INPUT IMAGE
# ---------------------------
image = input("Enter image path: ")

if not os.path.exists(image):
    print("Image not found!")
    exit()

print("\nRunning Snag Detection Pipeline...\n")


# ---------------------------
# VISION AGENT
# ---------------------------
result = detect_snag(image)

if "predictions" not in result:
    print("Model error:", result)
    exit()

predictions = result["predictions"]

print("Vision Agent completed")
print("Detections:", len(predictions))


# ---------------------------
# ANALYSIS AGENT
# ---------------------------
analysis = analyze(predictions)

predicted_severity = analysis["severity"]

if len(predictions) > 0:
    classes = [p["class"] for p in predictions]
    predicted_damage = max(set(classes), key=classes.count)
else:
    predicted_damage = "No Damage"

print("\nAnalysis Agent completed")
print("Severity:", predicted_severity)
print("Damage Type:", predicted_damage)


# ---------------------------
# IMAGE PROCESSING
# ---------------------------
img = cv2.imread(image)

if img is None:
    print("Error reading image")
    exit()

h, w = img.shape[:2]

preds = filter_predictions(predictions, w, h)
merged_box = merge_boxes(preds)


# ---------------------------
# FIRST OUTPUT (IMPORTANT)
# ---------------------------
draw_merged_box(image, merged_box, predicted_severity, predicted_damage)

report_file = "inspection_report.txt"
report = generate_report(predicted_damage, predicted_severity, image)

with open(report_file, "w") as f:
    f.write(report)

print("\nReport generated")
print("Saved as:", os.path.abspath(report_file))


subject, body, attachment = generate_email(
    predicted_damage,
    predicted_severity,
    image,
    report_file
)

email_file = "email_draft.txt"

with open(email_file, "w") as f:
    f.write("Subject: " + subject + "\n\n")
    f.write(body)

print("\nEmail draft generated")
print("Saved as:", os.path.abspath(email_file))


# ---------------------------
# FEEDBACK SECTION
# ---------------------------
print("\nFeedback Section")

user_input = input("Is prediction correct? (yes/no): ").strip().lower()

# ---------------------------
# CASE 1: WRONG PREDICTION
# ---------------------------
if user_input == "no":

    corrected_damage = input("Enter correct damage type: ")
    corrected_severity = input("Enter correct severity (Minor/Moderate/Severe): ")

    # ADD THIS
    corrected_bbox = get_bbox_from_user()

    # update values
    final_damage = corrected_damage
    final_severity = corrected_severity

    # CONVERT BBOX FORMAT (IMPORTANT)
    merged_box = {
        "x1": int(corrected_bbox["x"] - corrected_bbox["width"]/2),
        "y1": int(corrected_bbox["y"] - corrected_bbox["height"]/2),
        "x2": int(corrected_bbox["x"] + corrected_bbox["width"]/2),
        "y2": int(corrected_bbox["y"] + corrected_bbox["height"]/2)
    }

    # redraw image
    draw_merged_box(image, merged_box, final_severity, final_damage)

    # update report
    report = generate_report(final_damage, final_severity, image)
    with open(report_file, "w") as f:
        f.write(report)

    print("Updated report saved")

    # update email
    subject, body, attachment = generate_email(
        final_damage, final_severity, image, report_file
    )

    with open(email_file, "w") as f:
        f.write("Subject: " + subject + "\n\n")
        f.write(body)

    print("Updated email saved")

    # STORE FEEDBACK
    store_feedback(
        image,
        predictions,
        predicted_damage,
        corrected_damage,
        predicted_severity,
        corrected_severity,
        corrected_bbox   #IMPORTANT
    )

    print("Feedback stored (correction)")

# ---------------------------
# CASE 2: CORRECT PREDICTION
# ---------------------------
else:

    # STORE FEEDBACK (CORRECT CASE → reward)
    store_feedback(
        image,
        predictions,
        predicted_damage,
        predicted_damage,
        predicted_severity,
        predicted_severity,
        None
    )

    print("Feedback stored (correct prediction)")
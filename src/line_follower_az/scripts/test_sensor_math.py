#!/usr/bin/env python3
"""
Standalone sanity test for the line-detection math used inside
sensor_node.py's image_callback(). This does NOT need ROS2 or rclpy --
it builds synthetic grayscale images with a black line at a known x
position and checks that the weighted 5-zone algorithm reports an error
with the expected sign and a sane magnitude.

Run with: python3 scripts/test_sensor_math.py
"""
import numpy as np
import cv2


def compute_error(gray, num_zones=5, roi_top_fraction=0.55, threshold=90):
    height, width = gray.shape
    roi_start_row = int(height * roi_top_fraction)
    roi = gray[roi_start_row:height, :]
    _, mask = cv2.threshold(roi, threshold, 255, cv2.THRESH_BINARY_INV)

    zone_width = width // num_zones
    active = []
    for i in range(num_zones):
        zone = mask[:, i * zone_width:(i + 1) * zone_width]
        fraction_dark = float(np.count_nonzero(zone)) / float(zone.size + 1e-6)
        active.append(1 if fraction_dark > 0.12 else 0)

    half = num_zones // 2
    weights = list(range(-half, num_zones - half))
    active_count = sum(active)
    if active_count == 0:
        return None, active
    weighted_sum = sum(w * a for w, a in zip(weights, active))
    raw_error = weighted_sum / active_count
    return raw_error / float(half), active


def make_test_image(width, height, line_center_x, line_width=20):
    img = np.full((height, width), 220, dtype=np.uint8)  # light gray ground
    x0 = max(0, line_center_x - line_width // 2)
    x1 = min(width, line_center_x + line_width // 2)
    img[int(height * 0.55):, x0:x1] = 10  # dark line in the ROI band
    return img


WIDTH, HEIGHT = 320, 240
cases = [
    ("line far left", 20, "negative"),
    ("line center", WIDTH // 2, "zero-ish"),
    ("line far right", WIDTH - 20, "positive"),
    ("line slightly left of center", WIDTH // 2 - 60, "negative"),
]

print(f"{'case':32s} {'error':>8s}  {'expected sign':>14s}  {'active zones'}")
all_ok = True
for name, x, expected in cases:
    img = make_test_image(WIDTH, HEIGHT, x)
    error, active = compute_error(img)
    if error is None:
        print(f"{name:32s} {'NONE':>8s}  -> FAILED: no zone saw the line")
        all_ok = False
        continue
    sign_ok = (
        (expected == "negative" and error < -0.05) or
        (expected == "positive" and error > 0.05) or
        (expected == "zero-ish" and abs(error) < 0.4)
    )
    status = "OK" if sign_ok else "CHECK"
    if not sign_ok:
        all_ok = False
    print(f"{name:32s} {error:8.3f}  {expected:>14s}  {active}  [{status}]")

no_line_img = np.full((HEIGHT, WIDTH), 220, dtype=np.uint8)
error, active = compute_error(no_line_img)
print(f"\nno line visible -> error={error}, active_zones={active} "
      f"(expected: None, all-zero — sensor_node holds last known error in this case)")

print("\nRESULT:", "ALL CASES BEHAVED AS EXPECTED" if all_ok else "SOME CASES NEED REVIEW")

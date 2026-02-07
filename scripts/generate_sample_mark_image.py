from pathlib import Path
import numpy as np
import cv2

out = Path("sample_mark_teach.png")

# Create synthetic grayscale chip with marks
h, w = 300, 500
img = np.full((h, w), 230, dtype=np.uint8)

# Chip body
cv2.rectangle(img, (50, 60), (450, 240), 120, -1)

# Inner body
cv2.rectangle(img, (70, 80), (430, 220), 160, -1)

# Marks (white text)
font = cv2.FONT_HERSHEY_SIMPLEX
cv2.putText(img, "68C", (180, 175), font, 2.5, 240, 6, cv2.LINE_AA)

# Add a few holes/dots
cv2.circle(img, (120, 140), 6, 50, -1)
cv2.circle(img, (380, 140), 6, 50, -1)

# Add slight noise
noise = np.random.normal(0, 5, img.shape).astype(np.int16)
img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

# Save
cv2.imwrite(str(out), img)
print(out.resolve())

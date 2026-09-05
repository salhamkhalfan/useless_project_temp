# process.py

import cv2
import numpy as np


def clean_image(thresholded, min_area=20):

    # Input: veins = WHITE (255), background = BLACK (0).

    # Make it a 2D uint8 array if a path or 3-channel image is given.
    if isinstance(thresholded, str):
        thresholded = cv2.imread(thresholded, cv2.IMREAD_GRAYSCALE)
    elif thresholded.ndim == 3:
        thresholded = cv2.cvtColor(thresholded, cv2.COLOR_BGR2GRAY)

    # Foreground (veins) mask = white pixels.
    vein_mask = (thresholded > 0).astype(np.uint8)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        vein_mask,
        connectivity=8
    )

    # Start with black background
    cleaned = np.zeros_like(thresholded)

    for i in range(1, num_labels):

        area = stats[i, cv2.CC_STAT_AREA]

        if area >= min_area:
            # Keep this vein component WHITE
            cleaned[labels == i] = 255

    return cleaned
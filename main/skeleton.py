from skimage.morphology import skeletonize
import cv2
import numpy as np


def filter_skeleton_components(skeleton, min_px=200):
    # Keep only skeleton connected components containing at least min_px
    # pixels, dropping tiny fragments / noise islands.
    binary = skeleton.astype(np.uint8)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        binary, connectivity=8
    )
    keep = np.zeros_like(binary)
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= min_px:
            keep[labels == i] = 255
    return keep > 0


def _endpoints(binary):
    # binary: 0/1 uint8. Returns True where a skeleton pixel has
    # exactly one skeleton neighbour (a branch end).
    padded = np.pad(binary, 1, mode="constant").astype(np.uint8)
    kernel = np.ones((3, 3), np.uint8)
    kernel[1, 1] = 0
    neigh = cv2.filter2D(padded, -1, kernel, borderType=cv2.BORDER_CONSTANT)[1:-1, 1:-1]
    return (binary == 1) & (neigh == 1)


def prune_skeleton(skeleton, min_branch=8):
    # Repeatedly strip branch ends so short spurs disappear while the
    # true vein network is preserved.
    binary = skeleton.copy().astype(np.uint8)
    for _ in range(int(min_branch)):
        binary[_endpoints(binary)] = 0
    return binary > 0


def get_skeleton(cleaned_image, min_branch=8):

    # White pixels = veins
    binary = cleaned_image > 0

    # Remove tiny noise before skeletonization
    binary = binary.astype(np.uint8) * 255

    # Morphological opening removes tiny isolated noise
    kernel = np.ones((3, 3), np.uint8)
    binary = cv2.morphologyEx(
        binary,
        cv2.MORPH_OPEN,
        kernel
    )

    # Skeletonize
    skeleton = skeletonize(binary > 0)

    # Remove short spur branches
    skeleton = prune_skeleton(skeleton, min_branch)

    return skeleton
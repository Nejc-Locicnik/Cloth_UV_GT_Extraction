import cv2
from PIL import Image
import numpy as np
#import logging

#logging.basicConfig(level=logging.INFO)
#logger = logging.getLogger(__name__)
#logger.info("test")

def read_image(path:str) -> np.array:
    """
    Reads in and returns image (np.array) in BGR color space (OpenCV default).
    """

    return cv2.imread(path)

def save_image(img:np.array, path:str) -> None:
    image = Image.fromarray(img, mode='L')
    image.save(path)

def change_color_space(img:np.array, in_out_c_space:str = "BGR2RGB") -> np.array:
    """
    Performs the specified color space transformation on the input image.
    """
    
    selection = {
        "BGR2RGB" : cv2.COLOR_BGR2RGB,
        "BGR2HSV" : cv2.COLOR_BGR2HSV,
        "BGR2LAB" : cv2.COLOR_BGR2LAB,
        "HSV2RGB" : cv2.COLOR_HSV2RGB,
        "LAB2RGB" : cv2.COLOR_LAB2RGB
    }

    return cv2.cvtColor(img, selection[in_out_c_space])

def resize_image(img, size:tuple = (255, 255)) -> np.array:
    """
    Resizes the input image to the specified size.
    """

    return cv2.resize(img, size)

def cutout(img:np.array, x_coords:tuple, y_coords:tuple) -> np.array:
    """
    Cuts out the specified part (by x and y coordinates) of the input image.
    """

    x1, x2 = x_coords
    y1, y2 = y_coords
    return img[y1:y2, x1:x2] # potenially bugged and x and y need to be swapped

def denoise_mask(mask:np.array, kernel_sz:int=3, iter:int=1) -> np.array:
    """
    Denoise mask using morphologic operators (erode by kernel and then dilate). Repeat the specified amount.
    """

    kernel = np.ones((kernel_sz,)*2)
    eroded_mask = cv2.erode(mask, kernel, iterations=iter)
    dilated_mask = cv2.dilate(eroded_mask, kernel, iterations=iter)

    return dilated_mask

def match_delta_e_2000(img:np.array, color:np.array):
    """
    Calculate the Delta E 2000 color difference between an image and a specified color in the HSV color space.
    Applies a threshold to mark significant changes in a mask.
    """

    # Separate the specified color channels (H, S, V)
    H2, S2, V2 = color
    
    # Extract channels for the image and convert to float for accurate computation
    H1 = img[:, :, 0].astype(float)
    S1 = img[:, :, 1].astype(float)
    V1 = img[:, :, 2].astype(float)

    # Step 1: Calculate chroma for both colors
    C1 = np.sqrt(H1**2 + S1**2)
    C2 = np.sqrt(H2**2 + S2**2)

    # Step 2: Calculate the mean chroma
    C_mean = (C1 + C2) / 2.0

    # Step 3: Compute G, used to adjust the hue difference based on chroma
    G = 0.5 * (1 - np.sqrt(C_mean**7 / (C_mean**7 + 25**7)))

    # Step 4: Adjusted hue values
    H1_prime = H1 + G * H1
    H2_prime = H2 + G * H2

    # Step 5: Chroma prime
    C1_prime = np.sqrt(H1_prime**2 + S1**2)
    C2_prime = np.sqrt(H2_prime**2 + S2**2)

    # Step 6: Delta L, Delta C, and Delta H
    delta_L = V1 - V2
    delta_C = C1_prime - C2_prime
    delta_H = np.sqrt((H1_prime - H2_prime)**2 + (S1 - S2)**2) - delta_C

    # Step 7: Weighing factors for lightness, chroma, and hue
    L_mean = (V1 + V2) / 2.0
    S_L = 1 + (0.015 * ((L_mean - 50)**2) / np.sqrt(20 + (L_mean - 50)**2))
    S_C = 1 + 0.045 * C_mean
    S_H = 1 + 0.015 * C_mean

    # Step 8: Rotation term to handle unusual hue angles
    delta_theta = 30 * np.exp(-((H1_prime - H2_prime)**2) / 25)
    R_C = 2 * np.sqrt(C_mean**7 / (C_mean**7 + 25**7))
    R_T = -R_C * np.sin(2 * np.radians(delta_theta))

    # Step 9: Calculate final Delta E 2000
    delta_E = np.sqrt(
        (delta_L / S_L)**2 +
        (delta_C / S_C)**2 +
        (delta_H / S_H)**2 +
        R_T * (delta_C / S_C) * (delta_H / S_H)
    )

    # Step 10: Create a binary mask where Delta E is below the threshold
    #change_mask = (delta_E < threshold).astype(np.uint8) # Scale to 255 for an 8-bit mask
    #change_mask = delta_E
    return delta_E # return color distance

def hsv_match(img1:np.array, color:np.array) -> np.array:
    """
    Look at similarity between areas of the image and the specified colors in the HSV color space using
    the Hue channel. Simple Euclidean distance (^2 squared). Thershold the result on desired value.
    """

    img1 = img1.astype(int)
    change_mask = np.zeros((img1.shape[0], img1.shape[1]), dtype=np.uint8)
    H2, S2, V2 = color

    delta_H = img1[:, :, 0] - color[0]
    delta_S = img1[:, :, 1] - color[1]
    delta_V = img1[:, :, 2] - color[2]

    delta_e = np.sqrt(delta_H**2  + delta_S**2 + delta_V**2)

    #change_mask = (delta_e < threshold).astype(np.uint8)
    #change_mask = delta_e
    
    return delta_e # return color distance

def threshold_color_distance(distance, threshold):
    """Threshold the color distances to create a mask."""
    return (distance < threshold).astype(np.uint8)

def combine_masks(img, masks):
    """
    Combines multiple thresholded masks into a single mask. Color is encoded by index of target color.    
    """

    segmentation_mask = np.zeros_like(img, dtype=np.uint8)[:, :, 0]

    for i, mask in enumerate(masks):
        segmentation_mask += mask*(i+1)

    return segmentation_mask

def segment_mask_2_rgb_image(img, segment_mask):
    """
    Transform the combined mask with encoded values into an RGB image by mapping encoded values to specific colors.
    """

    color_map = {
        0: (0, 0, 0),
        1: (255, 0, 0),
        2: (0, 255, 0),
        3: (0, 0, 255),
        4: (255, 255, 0),
        5: (0, 255, 255),
        6: (255, 0, 255),
        7: (255, 255, 255)
    }

    rgb_mask = np.zeros_like(img, dtype=np.uint8)

    for val, color in color_map.items():
        val_mask = segment_mask.squeeze() == val
        rgb_mask[val_mask] = color

    return rgb_mask

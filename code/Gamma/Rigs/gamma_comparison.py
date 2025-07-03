import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import os

# Load the two gamma lookup table images
image1_path = "2025-05-22-SLAP2-gammalut.bmp"
image2_path = "2025-07-03-NP1-gammalut.bmp"

# Check if files exist
if not os.path.exists(image1_path):
    print(f"File not found: {image1_path}")
    exit()

if not os.path.exists(image2_path):
    print(f"File not found: {image2_path}")
    exit()

# Load images
img1 = Image.open(image1_path)
img2 = Image.open(image2_path)

# Convert to numpy arrays and get intensity values
# Since these are single row images, we'll take the first row
arr1 = np.array(img1)
arr2 = np.array(img2)

print(f"Image 1 shape: {arr1.shape}")
print(f"Image 2 shape: {arr2.shape}")

# Extract the single row of pixel intensities
# If the image is grayscale, use as is. If RGB, convert to grayscale
if len(arr1.shape) == 3:
    # RGB image - convert to grayscale
    intensities1 = np.mean(arr1[0], axis=1)  # Average RGB values for first row
else:
    # Grayscale image
    intensities1 = arr1[0]  # First row

if len(arr2.shape) == 3:
    # RGB image - convert to grayscale
    intensities2 = np.mean(arr2[0], axis=1)  # Average RGB values for first row
else:
    # Grayscale image
    intensities2 = arr2[0]  # First row

# Create x-axis (pixel positions)
x1 = np.arange(len(intensities1))
x2 = np.arange(len(intensities2))

# Create the plot
plt.figure(figsize=(12, 8))

# Plot both intensity profiles
plt.subplot(2, 1, 1)
plt.plot(x1, intensities1, 'b-', label='SLAP2 (2025-05-22)', linewidth=2)
plt.plot(x2, intensities2, 'r-', label='NP1 (2025-07-03)', linewidth=2)
plt.xlabel('Pixel Position')
plt.ylabel('Intensity')
plt.title('Gamma Lookup Table Comparison')
plt.legend()
plt.grid(True, alpha=0.3)

# Plot the difference
plt.subplot(2, 1, 2)
# Make sure both arrays have the same length for comparison
min_len = min(len(intensities1), len(intensities2))
diff = intensities1[:min_len] - intensities2[:min_len]
plt.plot(np.arange(min_len), diff, 'g-', linewidth=2)
plt.xlabel('Pixel Position')
plt.ylabel('Intensity Difference (SLAP2 - NP1)')
plt.title('Difference Between Gamma Lookup Tables')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# Print some statistics
print(f"\nSLAP2 intensity range: {np.min(intensities1):.2f} to {np.max(intensities1):.2f}")
print(f"NP1 intensity range: {np.min(intensities2):.2f} to {np.max(intensities2):.2f}")
print(f"Mean difference: {np.mean(diff):.2f}")
print(f"Max absolute difference: {np.max(np.abs(diff)):.2f}")

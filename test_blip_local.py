from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import torch

# Load model (first time will download to local cache)
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-large")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-large")

# Read image
image = Image.open("/Users/larryguo/HCI/HCI_Project/VLN4VI/Data/UCL EAST/Photo/IMG_6501.JPG").convert("RGB")

# Generate description
inputs = processor(image, return_tensors="pt")
out = model.generate(**inputs)
print(processor.decode(out[0], skip_special_tokens=True))

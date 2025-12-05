from vertexai.preview.vision_models import ImageGenerationModel
import vertexai
from google.oauth2 import service_account

import os
from dotenv import load_dotenv
load_dotenv()

credentials = None
service_account_path = 'backend/service-account-key.json'
if service_account_path and os.path.exists(service_account_path):
    print("[DEBUG] Path to service account exists")
    credentials = service_account.Credentials.from_service_account_file(
        service_account_path,
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    print("[DEBUG] Loaded credentials from service account file")

vertexai.init(project=os.getenv("VERTEX_PROJECT_ID"), location=os.getenv("VERTEX_PROJECT_LOCATION"), credentials=credentials)

model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")

def generate_image(prompt):
    try:
        images = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="16:9",
            safety_filter_level="block_some",
            person_generation="allow_adult"
        )
        return images[0]
    except Exception as e:
        print(f"Error: {e}")
        return None

# Usage
img = generate_image("A futuristic city with flying cars, photorealistic, 8k")
if img:
    img.save("output.png")
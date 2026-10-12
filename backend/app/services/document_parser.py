import re
import random
import logging

logger = logging.getLogger(__name__)

class AISimulatedParser:
    """
    Simulates an AI/OCR engine that extracts data from Bunker Delivery Notes (BDN).
    In a real production environment, this would call AWS Textract, Google Document AI,
    or a multimodal LLM like GPT-4o.
    """

    @staticmethod
    async def extract_fuel_data(filename: str, content_bytes: bytes) -> dict:
        """
        Simulates extracting structured data from a receipt image or PDF.
        Returns a dictionary with the extracted fields and a confidence score.
        """
        logger.info(f"AI parsing document: {filename} ({len(content_bytes)} bytes)")

        # Simulate processing delay
        import asyncio
        await asyncio.sleep(2)

        # We generate a mock extraction.
        # In reality, the AI would read the image pixels here.
        fuel_types = ["HFO", "MGO", "LNG", "Methanol"]
        ports = ["Rotterdam", "Singapore", "Shanghai", "Los Angeles", "Dubai"]

        extracted_data = {
            "fuel_type": random.choice(fuel_types),
            "fuel_consumed_mt": round(random.uniform(50.0, 500.0), 2),
            "departure_port": random.choice(ports),
            "arrival_port": random.choice(ports),
            "distance_nm": round(random.uniform(500.0, 3000.0), 2),
            "confidence_score": round(random.uniform(0.85, 0.99), 2),
            "raw_text_snippet": "BUNKER DELIVERY NOTE\\nSupplier: Marine Fuels Ltd...\\nQuantity Delivered..."
        }

        # Ensure ports are different
        while extracted_data["departure_port"] == extracted_data["arrival_port"]:
            extracted_data["arrival_port"] = random.choice(ports)

        logger.info(f"AI Extraction complete. Confidence: {extracted_data['confidence_score']}")
        return extracted_data

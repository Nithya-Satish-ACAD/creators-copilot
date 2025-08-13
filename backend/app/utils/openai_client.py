import os
from openai import OpenAI
from ..config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Guarantee the v2 header is set for all requests
os.environ["OPENAI_BETA_HEADER"] = "assistants=v2"

# Initialize client with v2 API header using settings
client = OpenAI(
    api_key=settings.OPENAI_API_KEY,
    default_headers={"OpenAI-Beta": "assistants=v2"}
)

logger.info("OpenAI client initialized with v2 API configuration")


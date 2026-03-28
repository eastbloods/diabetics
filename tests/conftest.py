import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from dotenv import load_dotenv
load_dotenv(override=False)

import models
from database import Base, engine
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
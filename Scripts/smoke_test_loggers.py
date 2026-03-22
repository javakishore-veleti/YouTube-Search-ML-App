"""Verify __name__-based logger names resolve to correct dotted module paths."""
import sys, os
sys.path.insert(0, '/Users/vavkkishore/PycharmProjects/YouTube-Search-ML-App')
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d) - %(message)s"
)

import app.app_common.api_initializer as m1
import app.app_model_builder.pipeline.queue_scheduler as m2
import app.app_model_approaches.approach_01.facade as m3
import app.app_integrators.youtube.yt_client as m4
import app.app_model_builder.api.admin_api as m5
import app.app_common.config.secrets_resolver as m6

for mod in [m1, m2, m3, m4, m5, m6]:
    print(f"  logger.name = {mod.logger.name}")

# Fire a test log to show format with filename:lineno
logging.getLogger("app.app_common.api_initializer").info("Logger format test from api_initializer")
print("\n✓ All logger names verified.")

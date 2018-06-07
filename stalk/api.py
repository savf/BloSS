import json

from flask import Flask, request
from flask_restful import abort

from configuration import Configuration
from logger import Logger
from pollen.attack_reporting import AttackReporting

logger = Logger("Stalk")

app = Flask(__name__)
config = Configuration()
attack_reporting = AttackReporting(config)
stalk_controller = None


@app.route("/api/v1.0/mitigate", methods=['POST'])
def mitigate():
    if not request.json:
        abort(400, message="No attack reports provided")
    json_data = json.loads(request.get_json(force=True))
    attack_report = (attack_reporting
                     .parse_attack_report_message(json_data))
    if stalk_controller is not None:
        stalk_controller.block_attackers(attack_report)
    else:
        logger.error("Stalk controller not configured")
        return "Stalk controller not configured", 500
    return "Accepted attackers for blocking", 202


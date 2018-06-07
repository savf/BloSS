from flask import Flask, request
from flask_restful import abort
from configuration import Configuration
from pollen.attack_reporting import AttackReporting
import json

app = Flask(__name__)
pollen_blockchain = None
config = Configuration()
attack_reporting = AttackReporting(config)


@app.route('/api/v1.0/report', methods=['POST'])
def report():
    if not request.json:
        abort(400, message="No attack reports provided")
    json_data = json.loads(request.get_json(force=True))
    attack_reports = []
    for message in json_data:
        attack_reports.append(attack_reporting
                              .parse_attack_report_message(message))
    try:
        pollen_blockchain.report_attackers(attack_reports)
    except:
        return "Failed to report attackers to blockchain", 500
    return "Successfully reported attackers to blockchain", 201


@app.route('/api/v1.0/set_blocked', methods=['POST'])
def set_blocked():
    if not request.json:
        abort(400, message="No hash provided.")
    json_data = json.loads(request.get_json(force=True))
    try:
        pollen_blockchain.set_blocked(json_data['hash'])
    except:
        return "Failed to mark attack report hash as blocked", 500
    return "Successfully marked attack report hash as blocked", 201
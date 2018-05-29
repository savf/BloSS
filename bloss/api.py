from flask import Flask, request
from flask_restful import abort
from configuration import Configuration
from pollen.attack_reporting import AttackReporting
from pollen.blockchain import PollenBlockchain

app = Flask(__name__)
pollen_blockchain = PollenBlockchain()
config = Configuration()
attack_reporting = AttackReporting(config)


@app.route('/api/v1.0/report', methods=['POST'])
def report():
    if not request.json:
        abort(400, message="No attack reports provided")
    json_data = request.get_json(force=True)
    attack_reports = {}
    for target, message in json_data.iteritems():
        attack_reports[target] = (attack_reporting
                                  .parse_attack_report_message(message))
    try:
        pollen_blockchain.report_attackers(attack_reports)
    except:
        return "Failed to report attackers to blockchain", 500
    return "Successfully reported attackers to blockchain", 201

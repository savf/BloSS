# The Blockchain Signaling System

Enabling cooperative, multi-domain DDoS defense by distributing attack reports through Ethereum among participating autonomous systems.

The entire system consists of three main components:
<p align="left">
<img align="left" width="300" src="./platform.svg">

**Stalk** monitors the network traffic of the underlying networking infrastructure

**Pollen** encapsulates all communication-related tasks, handling the database and Ethereum

**BloSS** is the core component which receives mitigation requests and signals ongoing attacks through *Pollen* and stops attack traffic through *Stalk*
</p>

<br/><br/><br/><br/><br/><br/><br/>
## Installation
### Python Prerequisites
The entire BloSS is written in Python 2.7, so you need to have a working Python installation as well as the required packages, which can be found in `python_requirements.txt` and can be installed through pip (you can get pip for example through `apt-get install python-pip`):

>`pip install -r python_requirements.txt`

### Configuration File
Create your custom `config.ini` file by looking at the `default_config.ini` template.

### System Components
You need a working instance of **InfluxDB** for statistical data to be stored and an **Ethereum blockchain** for the mitigation to work.

---

The current implementation does not yet support deploying the relay contract automatically. This means, you first need to deploy the `relay.sol` contract by hand, for example through the Remix IDE. Afterwards, you need to configure the relay contract in the `config.ini` of each controller by replacing the line from the default config:

>`RELAY_CONTRACT_ADDRESS = 0xDEADBEEFFEED`

with the actual contract address obtained through Remix.

*A small initial setup script will soon be provided that automatically deploys the relay contract.*

---

### Starting BloSS

After setting up all relevant components, you can directly start the entire system by issuing:

>`$ python runner.py --controller stalk/simple_router.py --controller stalk/controller.py`

Which starts both a simple packet-forwarding Ryu manager called SimpleRouter as well as the Stalk controller monitoring the network traffic.

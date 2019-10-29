import sqlite3 as sqlite
import json
import threading
from erc20tunnel import ERC20Tunnel
from wavesTunnel import WavesTunnel
from flask import Flask, render_template

app = Flask(__name__)

with open('config.json') as json_file:
    config = json.load(json_file)

@app.route('/')
def hello():
    heights = getHeights()

    return render_template('index.html', chainName = config['erc20']['name'],
                           wavesHeight = heights['Waves'],
                           ethHeight = heights['ETH'],
                           ethAddress = config['erc20']['gatewayAddress'],
                           wavesAddress = config['waves']['gatewayAddress'])

@app.route('/heights')
def getHeights():
    dbCon = sqlite.connect('gateway.db')

    result = dbCon.cursor().execute('SELECT chain, height FROM heights WHERE chain = "Waves" or chain = "ETH"').fetchall()

    return { result[0][0]: result[0][1], result[1][0]: result[1][1] }

@app.route('/ethAddress/<address>')
def getTunnelForETHAddress(address):
    dbCon = sqlite.connect('gateway.db')

    result = dbCon.cursor().execute('SELECT targetAddress FROM tunnel WHERE sourceAddress = "' + address + '"').fetchall()
    if len(result) == 0:
        targetAddress = None
    else:
        targetAddress = result[0][0]

    return { 'sourceAddress': address, 'targetAddress': targetAddress }

@app.route('/tunnel/<sourceAddress>/<targetAddress>')
def establishTunnel(sourceAddress, targetAddress):
    dbCon = sqlite.connect('gateway.db')

    dbCon.cursor().execute('INSERT INTO TUNNEL ("sourceAddress", "targetAddress") VALUES ("' + sourceAddress + '", "' + targetAddress + '")')
    dbCon.commit()

    return { 'successful': True }

def main():
    erc20Tunnel = ERC20Tunnel(config)
    wavesTunnel = WavesTunnel(config)
    wavesThread = threading.Thread(target=wavesTunnel.iterate)
    ercThread = threading.Thread(target=erc20Tunnel.iterate)
    wavesThread.start()
    ercThread.start()
    app.run(port=8080, host='0.0.0.0')

main()

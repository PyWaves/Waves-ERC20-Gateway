from web3 import Web3
import sqlite3 as sqlite
import requests
import time
import base58
import traceback
from ethtoken.abi import EIP20_ABI

class WavesTunnel(object):

    def __init__(self, config):
        self.config = config
        self.dbCon = sqlite.connect('gateway.db')

        self.w3 = Web3(Web3.HTTPProvider(self.config['erc20']['endpoint']))
        self.node = config['waves']['node']

        cursor = self.dbCon.cursor()
        self.lastScannedBlock = cursor.execute('SELECT height FROM heights WHERE chain = "Waves"').fetchall()[0][0]

    def getLatestBlockHeight(self):
        # height - 1 due to NG!
        latestBlock = requests.get(self.node + '/blocks/height').json()['height'] - 1

        return latestBlock

    def iterate(self):
        dbCon = sqlite.connect('gateway.db')

        while True:
            try:
                nextBlockToCheck = self.getLatestBlockHeight() - self.config['waves']['confirmations']

                if nextBlockToCheck > self.lastScannedBlock:
                    self.lastScannedBlock += 1
                    self.checkBlock(self.lastScannedBlock, dbCon)
                    cursor = dbCon.cursor()
                    cursor.execute('UPDATE heights SET "height" = ' + str(self.lastScannedBlock) + ' WHERE "chain" = "Waves"')
                    dbCon.commit()
            except Exception as e:
                self.lastScannedBlock -= 1
                print('Something went wrong during waves block iteration: ')
                print(traceback.TracebackException.from_exception(e))

            time.sleep(self.config['waves']['timeInBetweenChecks'])

    def checkBlock(self, heightToCheck, dbCon):
        print('checking waves block at: ' + str(heightToCheck))
        blockToCheck =  requests.get(self.node + '/blocks/at/' + str(heightToCheck)).json()
        for transaction in blockToCheck['transactions']:
            if transaction['type'] == 4 and transaction['recipient'] == self.config['waves']['gatewayAddress'] and transaction['assetId'] == self.config['waves']['assetId']:
                cursor = dbCon.cursor()
                targetAddress = base58.b58decode(transaction['attachment']).decode()
                if len(targetAddress) > 1 and self.txNotYetExecuted(transaction['id'], dbCon):
                    amount = transaction['amount'] / 10 ** self.config['waves']['decimals']
                    amount -= self.config['erc20']['fee']
                    amount *= 10 ** self.config['erc20']['contract']['decimals']
                    amount = int(amount)
                    token = self.w3.eth.contract(address=self.config['erc20']['contract']['address'], abi=EIP20_ABI)
                    nonce = self.w3.eth.getTransactionCount(self.config['erc20']['gatewayAddress'])
                    tx = token.functions.transfer(targetAddress, amount).buildTransaction({
                        'chainId': 1,
                        'gas': int(70000),
                        'gasPrice': self.w3.toWei(1, 'gwei'),
                        'nonce': nonce
                    })
                    signed_tx = self.w3.eth.account.signTransaction(tx, private_key=self.config['erc20']['privateKey'])
                    txId = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)
                    cursor.execute('INSERT INTO executed ("sourceAddress", "targetAddress", "wavesTxId", "ethTxId") VALUES ("' + transaction['sender'] + '", "' + targetAddress + '", "' + transaction['id'] + '", "' + txId.hex() + '")')
                    dbCon.commit()

    def txNotYetExecuted(self, transaction, dbCon):
        cursor = dbCon.cursor()
        result = cursor.execute('SELECT wavesTxId FROM executed WHERE wavesTxId = "' + transaction + '"').fetchall()

        return len(result) == 0

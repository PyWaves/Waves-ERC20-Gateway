from web3 import Web3
import sqlite3 as sqlite
import time
import pywaves as pw
import traceback
from ethtoken.abi import EIP20_ABI

class ERC20Tunnel(object):

    def __init__(self, config):
        self.config = config
        self.dbCon = sqlite.connect('gateway.db')
        self.w3 = self.getWeb3Instance()

        cursor = self.dbCon.cursor()
        self.lastScannedBlock = cursor.execute('SELECT height FROM heights WHERE chain = "ETH"').fetchall()[0][0]

    def getWeb3Instance(self):
        instance = None

        if self.config['erc20']['endpoint'].startswith('http'):
            instance = Web3(Web3.HTTPProvider(self.config['erc20']['endpoint']))
        else:
            instance = Web3()

        return instance

    def getLatestBlockHeight(self):
        latestBlock = self.w3.eth.blockNumber

        return latestBlock

    def getTransaction(self, id):
        result = None
        w3 = self.getWeb3Instance()
        transaction = w3.eth.getTransaction(id)

        if transaction['to'] == self.config['erc20']['contract']['address'] and transaction['input'].startswith('0xa9059cbb'):
            transactionreceipt = self.w3.eth.getTransactionReceipt(id)
            if transactionreceipt['status']:
                contract = w3.eth.contract(address=self.config['erc20']['contract']['address'], abi=EIP20_ABI)
                sender = transaction['from']
                decodedInput = contract.decode_function_input(transaction['input'])
                recipient = decodedInput[1]['_to']
                amount = decodedInput[1]['_value'] / 10 ** self.config['erc20']['contract']['decimals']
                result =  { 'sender': sender, 'function': 'transfer', 'recipient': recipient, 'amount': amount, 'token': self.config['erc20']['contract']['address'] }

        return result

    def iterate(self):
        dbCon = sqlite.connect('gateway.db')

        while True:
            try:
                nextBlockToCheck = self.getLatestBlockHeight() - self.config['erc20']['confirmations']

                if nextBlockToCheck > self.lastScannedBlock:
                    self.lastScannedBlock += 1
                    self.checkBlock(self.lastScannedBlock, dbCon)
                    cursor = dbCon.cursor()
                    cursor.execute('UPDATE heights SET "height" = ' + str(self.lastScannedBlock) + ' WHERE "chain" = "ETH"')
                    dbCon.commit()
            except Exception as e:
                print('Something went wrong during ETH block iteration: ')
                print(traceback.TracebackException.from_exception(e))

            time.sleep(self.config['erc20']['timeInBetweenChecks'])

    def checkBlock(self, heightToCheck, dbCon):
        print('checking eth block at: ' + str(heightToCheck))
        blockToCheck = self.w3.eth.getBlock(heightToCheck)
        for transaction in blockToCheck['transactions']:
            transactionInfo = self.getTransaction(transaction)

            if self.checkIfTransacitonValid(transactionInfo):
                cursor = dbCon.cursor()
                cursor.execute('SELECT targetAddress FROM tunnel WHERE sourceAddress ="' + transactionInfo['sender'] + '"')
                targetAddress = cursor.fetchall()[0][0]
                pw.setNode(node=self.config['waves']['node'], chain=self.config['waves']['network'])
                wavesAddress = pw.Address(seed = self.config['waves']['gatewaySeed'])
                amount = transactionInfo['amount'] - self.config['waves']['fee']
                if self.txNotYetExecuted(transaction.hex(), dbCon):
                    tx = wavesAddress.sendAsset(pw.Address(targetAddress), pw.Asset(self.config['waves']['assetId']), int(amount * 10 ** self.config['waves']['decimals']))
                    cursor.execute('INSERT INTO executed ("sourceAddress", "targetAddress", "wavesTxId", "ethTxId") VALUES ("' + transactionInfo['sender'] + '", "' + targetAddress + '", "' + tx['id'] + '", "' + transaction.hex() + '")')
                    cursor.execute('DELETE FROM tunnel WHERE sourceAddress ="' + transactionInfo['sender'] + '" AND targetAddress = "' + targetAddress + '"')
                    dbCon.commit()

    def txNotYetExecuted(self, transaction, dbCon):
        cursor = dbCon.cursor()
        result = cursor.execute('SELECT wavesTxId FROM executed WHERE ethTxId = "' + transaction + '"').fetchall()

        return len(result) == 0

    def checkIfTransacitonValid(self, transactionInfo):
        return transactionInfo != None and \
               transactionInfo['function'] == 'transfer' and \
               transactionInfo['recipient'] == self.config['erc20']['gatewayAddress'] and \
               transactionInfo['token'] == self.config['erc20']['contract']['address']

import pandas as pd
import sqlite3

def transactions(csvPath, databasePaths):
    # Import csv to DF:
    df = pd.read_csv(csvPath)
    df.columns = ['Date', 'Time', 'Type', 'Reference', 'Description', 'MiscFees', 'Commissions', 'Amount', 'Balance']

    # Clean and Output:
    dfClean = df.copy()
    dfClean['feesAndCommissions'] = dfClean['MiscFees'] + dfClean['Commissions']
    dfClean = dfClean[(dfClean['Type'] == 'TRD') | (dfClean['Type'] == 'RAD')]
    dfClean = dfClean[['Date', 'Time', 'Description', 'feesAndCommissions', 'Amount']]
    dfClean.to_csv(csvPath, index=False)

    # Store in Master and Backup Database:
    for x in databasePaths:
        conn = sqlite3.connect(x)
        conn.execute("""CREATE TABLE IF NOT EXISTS transactions (Date TEXT, Time TEXT, Type TEXT, Reference INTEGER, Description TEXT,
                        MiscFees REAL, Commissions REAL, Amount REAL, Balance REAL)""")
        conn.execute("""CREATE TABLE IF NOT EXISTS cleanTransactions (Date TEXT, Time TEXT, Description TEXT,
                                feesAndCommissions REAL, Amount REAL)""")
        df.to_sql('transactions', conn, index=False, if_exists='append')
        dfClean.to_sql('cleanTransactions', conn, index=False, if_exists='append')
        conn.commit()
        conn.close()


class trade:
    def __init__(self):
       self.trader = 'None'
       self.types = 'None'
       self.tickers = 'None'
       self.options = 'None'
       self.expectedRisk = 'None'
       self.maxRisk = 'None'
       self.notes = 'None'
       self.description = ''
       self.dateOpen = 'None'
       self.dateClose = 'None'
       self.timeOpen = 'None'
       self.timeClose = 'None'
       self.feesAndCommissions = 'None'
       self.grossPL = 'None'
       self.netPL = 'None'
       self.returnOnExpectedRisk = 'None'
       self.returnOnMaxRisk = 'None'
       self.transactions = []
       self.tradeSummary = 'None'
       
        
    def inputs(self, trader=None, types=None, tickers=None, options=None, expectedRisk=None, maxRisk=None, notes=None):
        self.trader = trader
        self.types = types
        self.tickers = tickers
        self.notes = notes
        self.expectedRisk = expectedRisk
        self.maxRisk = maxRisk
        self.options = options
        
    
    def addTransaction(self, date, time, description, fc, amount):
        transactionList = [date, time, description, fc, amount]
        self.transactions.append(transactionList)

    def close(self):
        #Set Final Variables
        df = pd.DataFrame(self.transactions)
        df.columns = ['Date', 'Time', 'Description', 'feesAndCommissions', 'Amount']
        for x in df['Description']:
            self.description += '{}, '.format(x)
        self.dateOpen = df['Date'].iloc[0]
        self.dateClose = df['Date'].iloc[-1]
        self.timeOpen = df['Time'].iloc[0]
        self.timeClose = df['Time'].iloc[-1]
        self.feesAndCommissions = sum(df['feesAndCommissions'])
        self.grossPL = sum(df['Amount'])
        self.netPL = self.feesAndCommissions + self.grossPL
        self.grossReturnOnExpectedRisk = self.grossPL / self.expectedRisk * -1
        self.netReturnOnExpectedRisk = self.netPL / self.expectedRisk * -1
        self.grossReturnOnMaxRisk = self.grossPL / self.maxRisk * -1
        self.netreturnOnMaxRisk = self.netPL / self.maxRisk * -1
        self.tradeSummary = [self.trader, self.types, self.tickers, self.options,
                                self.expectedRisk, self.maxRisk, self.notes,  self.description, self.dateOpen,
                                self.dateClose, self.timeOpen, self.timeClose, self.feesAndCommissions, self.grossPL,
                                self.netPL, self.grossReturnOnExpectedRisk, self.netReturnOnExpectedRisk,
                                self.grossReturnOnMaxRisk, self.netreturnOnMaxRisk]

    def save(self, databasePaths):
        for x in databasePaths:
            conn = sqlite3.connect(x)
            conn.execute('''CREATE TABLE IF NOT EXISTS fullTrades(Trader TEXT, Types TEXT, Tickers TEXT, Options TEXT, ExpectedRisk REAL, MaxRisk REAL,
                                Notes TEXT, Date TEXT, Time TEXT, Description TEXT, FeesAndCommissions REAL, Amount REAL)''')
            conn.execute('''INSERT INTO fullTrades (Trader, Types, Tickers, Options, ExpectedRisk, MaxRisk, Notes) VALUES(?, ?, ?, ?, ?, ?, ?)''',
                         (self.trader, self.types, self.tickers, self.options, self.expectedRisk, self.maxRisk, self.notes,))
            df = pd.DataFrame(self.transactions)
            for x in range(len(df)):
                date, time, description, fc, amount = df.iloc[x]
                conn.execute('''INSERT INTO fullTrades (Date, Time, Description, FeesAndCommissions, Amount) VALUES (?, ?, ?, ?, ?)''',
                             (date, time, description, fc, amount))
            conn.execute('''CREATE TABLE IF NOT EXISTS tradeSummaries (Trader TEXT, Types TEXT, Tickers TEXT, Options TEXT, ExpectedRisk REAL,
                                MaxRisk REAL, Notes TEXT, Description TEXT, OpenDate TEXT, CloseDate TEXT, OpenTime TEXT, 
                                CloseTime TEXT, FeesAndCommissions REAL, GrossPL REAL, NetPL REAL, GrossReturnOnExpectedRisk REAL,
                                NetReturnOnExpectedRisk REAL, GrossReturnOnMaxRisk REAL, NetReturnOnMaxRisk REAL)''')
            conn.execute('''INSERT INTO tradeSummaries (Trader, Types, Tickers, Options, ExpectedRisk, MaxRisk,
                                Notes, Description, OpenDate, CloseDate, OpenTime, CloseTime, FeesAndCommissions, GrossPL, NetPL, 
                                GrossReturnOnExpectedRisk, NetReturnOnExpectedRisk, GrossReturnOnMaxRisk, NetReturnOnMaxRisk) 
                                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                (self.trader, self.types, self.tickers, self.options,
                                self.expectedRisk, self.maxRisk, self.notes,  self.description, self.dateOpen,
                                self.dateClose, self.timeOpen, self.timeClose, self.feesAndCommissions, self.grossPL,
                                self.netPL, self.grossReturnOnExpectedRisk, self.netReturnOnExpectedRisk,
                                self.grossReturnOnMaxRisk, self.netreturnOnMaxRisk))
            conn.commit()
            conn.close()




def processTradeQueue(csvPath, databasePaths, clearQueue=False):
    '''This function processes the excel trade Queue, giving final stats and saving them to a database.
    This is a sub-optimal function for this task because it utilizes the 'trade' class, which was written expressly
    to be used in conjunction with a GUI on single trades. Until I get the GUI up and running though, Excel files and
    this function are the placeholder. '''

    batch = []
    df = pd.read_csv(csvPath)
    df['TRADER'].fillna('LEG', inplace=True)
    fillZero = ['EXPECTED', 'MAX', 'F&C', 'AMOUNT']
    for z in fillZero:
        df[z].fillna(0, inplace=True)
    # df2 = pd.DataFrame(['END'], columns=['TRADER'])
    # df = df.append(df2)

    tradeOn = False
    for x in range(len(df)):
        trader, types, tickers, options, expected, max, notes, date, time, description, fc, amount = df.iloc[x]
        if df['TRADER'].iloc[x] == 'END':
            thisTrade.close()
            batch.append(thisTrade.tradeSummary)
            thisTrade.save(databasePaths)
            print('Trade Queue processed. Please move trades from Trade Queue to All Trades.')
            print('Please set end = False')
            print('Please reset Workspace variables.')
            break
        elif df['TRADER'].iloc[x] != 'LEG':
            if tradeOn == True:
                thisTrade.close()
                batch.append(thisTrade.tradeSummary)
                thisTrade.save(databasePaths)
            tradeOn = True
            thisTrade = trade()
            thisTrade.inputs(trader, types, tickers, options, expected, max, notes)
        else:
            thisTrade.addTransaction(date, time, description, fc, amount)

    if clearQueue == True:
        df = pd.DataFrame(columns = ['TRADER', 'TYPES', 'TICKERS', 'OPTIONS', 'EXPECTED', 'MAX', 'NOTES', 'DATE', 'TIME',
                   'DESCRIPTION', 'F&C', 'AMOUNT'])
        df.to_csv(csvPath, index = False)

    batchReport = pd.DataFrame(batch, columns = ['TRADER', 'TYPES', 'TICKERS', 'OPTIONS', 'EXPECTED', 'MAX', 'NOTES',
                                                 'DESCRIPTION', 'OPEN DATE', 'CLOSE DATE', 'OPEN TIME', 'CLOSE TIME',
                                                 'FEES AND COMMISSIONS', 'GROSS PL', 'NET PL', 'GROSS RETURN ON EXPECTED RISK',
                                                 'NET RETURN ON EXPECTED RISK', 'GROSS RETURN ON MAX RISK',
                                                 'NET RETURN ON MAX RISK'])
    batchReport.to_csv('batchReport.csv', index = False)


def sqlToDataFrame(databasePath, tableName):
    conn = sqlite3.connect(databasePath)
    string = "SELECT * FROM {}".format(tableName)
    df = pd.read_sql_query(string, conn)
    return df


def replaceTable(databasePaths, tableName, csvPath):
    renameString = "ALTER TABLE {} RENAME TO temporaryOldTable".format(tableName)
    df = pd.read_csv(csvPath)
    for database in databasePaths:
        conn = sqlite3.connect(database)
        conn.execute(renameString)
        df.to_sql(tableName, conn, index=False)
        conn.commit()
        conn.close()

    print('Process Complete: Verify Accuracy then manually delete temporaryOldTable')











        

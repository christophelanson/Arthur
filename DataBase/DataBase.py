from PyQt5 import QtSql, QtGui
from colorama import Fore

class DataBase:

    def __init__(self, listSensor):

        self.listSensor = listSensor
        self.db = QtSql.QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName('robotDb.sqlite')
        if not self.db.open():
            print(f"{Fore.RED}ERROR (hardwareHandler) -> Error while lauching database")
        else:
            print("Database open")
        
        self.query = QtSql.QSqlQuery()

        query = "DROP TABLE SensorValue"
        self.query.exec_(query)
        
        
        query = "CREATE TABLE SensorValue (sensor varchar(20), value varchar(20))"
        self.query.exec_(query)
        self.insertSensorValue(self.listSensor)


    def insertSensorValue(self, listSensor):
        for sensor in listSensor:
            request = "INSERT OR REPLACE INTO SensorValue (sensor, value) " "VALUES ('"+str(sensor)+"', 0)"
            self.query.exec_(request)
    
    def updateSensorValue(self, sensor, value): 
        request = "UPDATE SensorValue SET value ='"+str(value)+"'WHERE sensor ='"+str(sensor)+"'"
        self.query.exec_(request)

    def getSensorValue(self, sensor):
        self.query.exec("SELECT sensor, value FROM SensorValue")
        while(self.query.next()):
            if self.query.value(0) == sensor:
                return self.query.value(1)


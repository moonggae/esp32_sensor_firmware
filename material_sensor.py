from machine import ADC

class MaterialSensor:

    def __init__(self, pin):
        self.pin = pin


    def read_votage(self):
        return ADC(self.pin).read()

    def read_resistance(self):
        voltage = self.read_votage()
        return (voltage * 1000) / (3.3 - voltage)
from machine import ADC

class MaterialSensor:

    def __init__(self, pin):
        self.pin = pin


    def read(self):
        ADC(self.pin).read() * 3.3 / 4095

import logging
import time
import can, cantools
import j1939

logging.getLogger('j1939').setLevel(logging.DEBUG)
logging.getLogger('can').setLevel(logging.DEBUG)

class J1939Reader(j1939.ControllerApplication):
    """CA to produce messages

    This CA produces simulated sensor values and cyclically sends them to
    the bus with the PGN 0xFEF6 (Intake Exhaust Conditions 1).
    """

    def __init__(self, cfg, rxqueue, mapper):
        # compose the name descriptor for the new ca
        name = j1939.Name(
            arbitrary_address_capable=0,
            industry_group=j1939.Name.IndustryGroup.Industrial,
            vehicle_system_instance=1,
            vehicle_system=1,
            function=1,
            function_instance=1,
            ecu_instance=1,
            manufacturer_code=666,
            identity_number=1234567
            )
        device_address_preferred = 128
        # old fashion calling convention for compatibility with Python2
        j1939.ControllerApplication.__init__(self, name, device_address_preferred)
        # adaptation
        self.queue=rxqueue
        self.cfg=cfg
        self.db = cantools.database.load_file(cfg['vss.dbcfile'])
        self.mapper=mapper
        self.canidwl = self.get_whitelist()
        self.parseErr=0

    def start(self):
        """Starts the CA
        (OVERLOADED function)
        """
        # add our timer event
        self._ecu.add_timer(0.500, self.timer_callback)
        # call the super class function
        return j1939.ControllerApplication.start(self)

    def timer_callback(self, cookie):
        """Callback for sending the IEC1 message

        This callback is registered at the ECU timer event mechanism to be
        executed every 500ms.

        :param cookie:
            A cookie registered at 'add_timer'. May be None.
        """
        # wait until we have our device_address
        if self.state != j1939.ControllerApplication.State.NORMAL:
            # returning true keeps the timer event active
            return True

        pgn = j1939.ParameterGroupNumber(0, 0xFE, 0xF6)
        data = [
            j1939.ControllerApplication.FieldValue.NOT_AVAILABLE_8, # Particulate Trap Inlet Pressure (SPN 81)
            j1939.ControllerApplication.FieldValue.NOT_AVAILABLE_8, # Boost Pressure (SPN 102)
            j1939.ControllerApplication.FieldValue.NOT_AVAILABLE_8, # Intake Manifold 1 Temperature (SPN 105)
            j1939.ControllerApplication.FieldValue.NOT_AVAILABLE_8, # Air Inlet Pressure (SPN 106)
            j1939.ControllerApplication.FieldValue.NOT_AVAILABLE_8, # Air Filter 1 Differential Pressure (SPN 107)
            j1939.ControllerApplication.FieldValue.NOT_AVAILABLE_16_ARR[0], # Exhaust Gas Temperature (SPN 173)
            j1939.ControllerApplication.FieldValue.NOT_AVAILABLE_16_ARR[1],
            j1939.ControllerApplication.FieldValue.NOT_AVAILABLE_8, # Coolant Filter Differential Pressure (SPN 112)
            ]

        # SPN 105, Range -40..+210
        # (Offset -40)
        receiverTemperature = 30
        data[2] = receiverTemperature + 40

        self.send_message(6, pgn.value, data)

        # returning true keeps the timer event active
        return True

    def get_whitelist(self):
        print("Collecting signals, generating CAN ID whitelist")
        wl = []
        for entry in self.mapper.map():
            canid=self.get_canid_for_signal(entry[0])
            if canid != None and canid not in wl:
                wl.append(canid)
        return wl

    def get_canid_for_signal(self, sig_to_find):
        for msg in self.db.messages:
            for signal in msg.signals:
                if signal.name == sig_to_find:
                    id = msg.frame_id
                    print("Found signal {} in CAN frame id 0x{:02x}".format(signal.name, id))
                    return id
        print("Signal {} not found in DBC file".format(sig_to_find))
        return None

    def start_listening(self):
        print("Open CAN device {}".format(self.cfg['can.port']))
        # create the ElectronicControlUnit (one ECU can hold multiple ControllerApplications)
        ecu = j1939.ElectronicControlUnit()
        
        # Connect to the CAN bus
        ecu.connect(bustype='socketcan', channel=self.cfg['can.port'])
        # add CA to the ECU
        ecu.add_ca(controller_application=self)
        self.start()
        

    def on_message(self, pgn, data):
        #msg = self._ecu._bus.recv()

        if len(data) > 8:

            if str(pgn) == "65251":
                self.decode_data(pgn, data)
            #print("PGN: " + str(pgn))
            #print("DATA: " + str(data))

        #try:
        #    decode=self.db.decode_message(msg.arbitration_id, msg.data)
        #    #print("Decod" +str(decode))
        #    rxTime=time.time()
        #    for k,v in decode.items():
        #        if k in self.mapper:
        #            if self.mapper.minUpdateTimeElapsed(k, rxTime):
        #                self.queue.put((k,v))
        #except Exception as e:
        #    self.parseErr+=1
        #    #print("Error Decoding: "+str(e))

    def decode_data(self, pgn, data):
        # INTEL - LITTLE ENDIAN > DECIMAL * FACTOR
        if str(pgn) == "65251":
            # EngSpeedAtIdlePoint1
            b1 = data[0]
            b2 = data[1]
            print("Second Byte: " + str(b2) + ", First Byte: " + str(b1))

            # EngSpeedAtPoint2

            # EngReferenceTorque


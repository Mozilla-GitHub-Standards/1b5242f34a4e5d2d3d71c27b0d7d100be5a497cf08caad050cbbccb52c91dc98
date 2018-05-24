from action import Action
from event import Event
from property import Property
from thing import Thing
from value import Value
from server import MultipleThings, WebThingServer
import logging
import random
import time
import uuid

log = logging.getLogger(__name__)


class OverheatedEvent(Event):

    def __init__(self, thing, data):
        Event.__init__(self, thing, 'overheated', data=data)


class FadeAction(Action):

    def __init__(self, thing, input_):
        Action.__init__(self, uuid.uuid4().hex, thing, 'fade', input_=input_)

    def perform_action(self):
        time.sleep(self.input['duration'] / 1000)
        self.thing.set_property('level', self.input['level'])
        self.thing.add_event(OverheatedEvent(self.thing, 102))


class ExampleDimmableLight(Thing):
    """A dimmable light that logs received commands to stdout."""

    def __init__(self):
        Thing.__init__(self,
                       'My Lamp',
                       'dimmableLight',
                       'A web connected lamp')

        self.add_available_action(
            'fade',
            {'description': 'Fade the lamp to a given level',
             'input': {
                 'type': 'object',
                 'required': [
                     'level',
                     'duration',
                 ],
                 'properties': {
                     'level': {
                         'type': 'number',
                         'minimum': 0,
                         'maximum': 100,
                     },
                     'duration': {
                         'type': 'number',
                         'unit': 'milliseconds',
                     },
                 },
             }},
            FadeAction)

        self.add_available_event(
            'overheated',
            {'description':
             'The lamp has exceeded its safe operating temperature',
             'type': 'number',
             'unit': 'celsius'})

        self.add_property(self.get_on_property())
        self.add_property(self.get_level_property())

    def get_on_property(self):
        return Property(self,
                        'on',
                        Value(True, lambda v: print('On-State is now', v)),
                        metadata={
                            'type': 'boolean',
                            'description': 'Whether the lamp is turned on',
                        })

    def get_level_property(self):
        return Property(self,
                        'level',
                        Value(50, lambda l: print('New light level is', l)),
                        metadata={
                            'type': 'number',
                            'description': 'The level of light from 0-100',
                            'minimum': 0,
                            'maximum': 100,
                        })


class FakeGpioHumiditySensor(Thing):
    """A humidity sensor which updates its measurement every few seconds."""

    def __init__(self):
        Thing.__init__(self,
                       'My Humidity Sensor',
                       'multiLevelSensor',
                       'A web connected humidity sensor')

        self.add_property(
            Property(self,
                     'on',
                     Value(True),
                     metadata={
                         'type': 'boolean',
                         'description': 'Whether the sensor is on',
                     }))

        self.level = Value(0.0)
        self.add_property(
            Property(self,
                     'level',
                     self.level,
                     metadata={
                         'type': 'number',
                         'description': 'The current humidity in %',
                         'unit': '%',
                     }))

        log.debug('starting the sensor update looping task')

    @staticmethod
    def read_from_gpio():
        """Mimic an actual sensor updating its reading every couple seconds."""
        return 70.0 * random.random() * (-0.5 + random.random())


def run_server():
    log.info('run_server')

    # Create a thing that represents a dimmable light
    light = ExampleDimmableLight()

    # Create a thing that represents a humidity sensor
    sensor = FakeGpioHumiditySensor()

    # If adding more than one thing, use MultipleThings() with a name.
    # In the single thing case, the thing's name will be broadcast.
    server = WebThingServer(MultipleThings([light, sensor],
                                           'LightAndTempDevice'),
                            port=80)
    try:
        log.info('starting the server')
        server.start()
    except KeyboardInterrupt:
        log.info('stopping the server')
        server.stop()
        log.info('done')


if __name__ == '__main__':
    log.basicConfig(
        level=10,
        format="%(asctime)s %(filename)s:%(lineno)s %(levelname)s %(message)s"
    )
    run_server()

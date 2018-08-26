from random import random


class EventManager:
    def __init__(self, jitter=0.1):
        self.events = []
        self.jitter = jitter

    def add_event(self, callback, time_inverval=1.0, jitter=None):
        time = time_inverval
        self.events.append({
            'callback': callback,
            'time_inverval': time,
            'time': 0})

        print(self.events)

    def get_current_events(self, current_time):
        events_to_run = []

        for event in self.events:
            callback = event['callback']
            time_inverval = event['time_inverval']
            time = event['time']

            if current_time - time > time_inverval:
                # print("%7.2f %7.2f %7.2f %7.2f " % (time_inverval, time, current_time, current_time - time))
                event['time'] = current_time
                events_to_run.append(callback)

        return events_to_run

from random import random


class EventManager:
    def __init__(self, jitter=0.5):
        self.events = []
        self.jitter = jitter

    def add_event(self, callback, time_inverval):
        self.events.append({
            'callback': callback,
            'time_inverval': time_inverval + ((random() - 0.5) * 2.0) * self.jitter,
            'time': 0})

    def get_current_events(self, current_time):
        events_to_run = []

        for event in self.events:
            callback = event['callback']
            time_inverval = event['time_inverval']
            time = event['time']

            if current_time - time > time_inverval:
                event['time'] = current_time
                events_to_run.append(callback)

        return events_to_run

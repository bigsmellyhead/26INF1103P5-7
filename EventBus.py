from EventName import EventName
from collections.abc import Callable
from typing import Any

class EventBus:
    #Set up callback functions to call when event is triggered
    #Event_list is a dictionary containing events to a list of callback functions
    #that take in one parameter of type Data and return nothing
    event_list: dict[EventName, list[Callable[[Any]],None]]

    #Store List of Active Events
    #(event: str, event_data: Data)
    #active_events: list[tuple[EventName, Data]]

    #Initialise Bus
    def __init__(self):
        self.event_list = {}
        #self.active_events = []

    # Raise Events
    def raise_event(self, event: EventName, event_data: str):
        if event not in self.event_list:
            raise ValueError(f"Event '{event}' is not registered.")
        
        else:
            self.active_events.append((event, event_data))


    # Subscription of Events
    def subscribe_event(self, event: EventName, callback: Callable[[str]]):
        # Event not inside
        if event not in self.event_list:
            self.event_list[event] = [callback]
        # Event is inside
        else:
            self.event_list[event].append(callback) 


    # Handles the calling of callback func attached to events
    def update(self):
        if len(self.active_events) > 0:
            event, data = self.active_events.pop(0)
            if event not in self.event_list:
                raise ValueError(f"Event '{event}' is not registered.")

            for callback in self.event_list[event]:
                callback(data)


#Global Definiton of Bus
event_bus = EventBus()
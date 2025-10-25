package regulation

import (
	"encoding/json"
	"time"

	"github.com/verticedev/coagulation/pkg/eventbus"
)

// createEvent creates typed Event from map payload.
func createEvent(eventType string, data map[string]interface{}) *eventbus.Event {
	// Serialize map to JSON bytes for Payload field
	payload, _ := json.Marshal(data)
	return &eventbus.Event{
		Type:      eventType,
		Timestamp: time.Now(),
		Payload:   payload,
	}
}

// eventToMap extracts Payload field from Event as map.
func eventToMap(event *eventbus.Event) map[string]interface{} {
	if event == nil || event.Payload == nil {
		return make(map[string]interface{})
	}
	var dataMap map[string]interface{}
	if err := json.Unmarshal(event.Payload, &dataMap); err != nil {
		return make(map[string]interface{})
	}
	return dataMap
}

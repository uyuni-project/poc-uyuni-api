package uyuniapi

import (
	"reflect"
)

type DataAggregator struct {
	vidman *VIDManager
	shards map[string]interface{}
}

// Constructor
func NewDataAggregator(vidmanager *VIDManager) *DataAggregator {
	agr := new(DataAggregator)
	agr.vidman = vidmanager
	agr.shards = make(map[string]interface{})

	return agr
}

// Aggregate
func (agr *DataAggregator) aggregate(fqdn string, data interface{}) {
	agr.shards[fqdn] = data
}

// Multiplex data from different sources into one
func (agr *DataAggregator) Multiplex() interface{} {
	data, merged := agr.mergeStructs()
	if !merged {
		data = nil
	}

	return data
}

func (agr *DataAggregator) mergeStructs() (interface{}, bool) {
	var data interface{} = nil
	if len(agr.shards) > 0 {
		for _, rpcRef := range agr.vidman.GetContextFQDNs() {
			res := agr.shards[rpcRef]
			if reflect.TypeOf(res).Kind() == reflect.Slice {
				if data == nil {
					data = make([]interface{}, 0)
				}

				for _, dataRef := range res.([]interface{}) {
					if reflect.TypeOf(dataRef).Kind() == reflect.Map {
						data = append(data.([]interface{}), agr.remapIds(rpcRef, dataRef))
					}
				}
			}
		}
	}

	return data, data != nil
}

// Remap system IDs
func (agr *DataAggregator) remapIds(context string, data interface{}) interface{} {
	var rData interface{} = data
	if reflect.TypeOf(data).Kind() == reflect.Map {
		if systemId, ok := data.(map[string]interface{})["id"]; ok { // TODO: check if it is really string/interface map
			data.(map[string]interface{})["id"] = agr.vidman.GetContext(context).ToVirtualId(int(systemId.(int64)))
		}
	}
	return rData
}

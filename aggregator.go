package uyuniapi

import (
	"github.com/davecgh/go-spew/spew"
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
	data := make([]interface{}, 0)
	return data
}

func (agr *DataAggregator) mergeStructs() (interface{}, bool) {
	merged := false
	if len(agr.shards) > 0 {
		//if reflect.TypeOf(agr.vidman.GetContextFQDNs()[0]) ==
		spew.Dump(agr.vidman.GetContextFQDNs()[0])
	}

	return nil, merged
}

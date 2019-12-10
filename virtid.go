package uyuniapi

import (
	"fmt"
	"strconv"
)

// Virtual ID manager
type VIDManager struct {
	umap  map[string]int
	urmap map[int]string
}

func NewVIDManager() *VIDManager {
	vidman := new(VIDManager)
	vidman.umap = make(map[string]int)
	vidman.urmap = make(map[int]string)

	return vidman
}

// Add context
func (vidman *VIDManager) AddContext(fqdn string) {
	vidman.umap[fqdn] = len(vidman.umap) + 1
	vidman.urmap[vidman.umap[fqdn]] = fqdn
}

// Get context
func (vidman *VIDManager) GetContext(fqdn string) *VIDContext {
	var vid *VIDContext
	if fqdn_id, exist := vidman.umap[fqdn]; exist {
		vid = NewVIDContext(fqdn_id, len(vidman.umap))
	} else {
		panic("Context not found")
	}

	return vid
}

// Decode virtual ID and map to the FQDN of the context server
func (vidman *VIDManager) ToSystemId(vsysid int) (int, string) {
	vids := strconv.Itoa(vsysid)[1:]
	ctxdgt := len(strconv.Itoa(len(vidman.umap)))
	ctx, _ := strconv.Atoi(vids[:ctxdgt])
	sid, _ := strconv.Atoi(vids[ctxdgt:])

	return sid, vidman.urmap[ctx]
}

// Return all known contexts to the VID manager
func (vidman *VIDManager) GetContextFQDNs() []string {
	ctx := make([]string, len(vidman.umap))
	idx := 0
	for fqdn := range vidman.umap {
		ctx[idx] = fqdn
		idx++
	}

	return ctx
}

// ID calculations
type VIDContext struct {
	max     int
	context int
}

// Constructor
func NewVIDContext(context int, max int) *VIDContext {
	idc := new(VIDContext)
	idc.context = context
	idc.max = max

	return idc
}

// Max width for context zero padding
func (idc *VIDContext) ctxDigits() string {
	return strconv.Itoa(len(strconv.Itoa(idc.max)))
}

/*
Translation to the Virtual ID. The virtual ID consistsof
the following format:

	 1 [max] [System ID]
	 ^  ^     ^
	 |  |     |
	 |  |     +--- A regular Uyuni ID
	 |  +--------- Maximum number of Uyuni servers. Smaller numbers are padded with zero.
	 +------------ Always 1
*/
func (idc *VIDContext) ToVirtualId(systemid int) int {
	ptn := "1%0" + idc.ctxDigits() + "d"
	vid, _ := strconv.Atoi(fmt.Sprintf(ptn+"%d", idc.context, systemid))

	return vid
}

// Extract system ID within the given context
func (idc *VIDContext) ToSystemId(vsysid int) int {
	vids := strconv.Itoa(vsysid)[1:]
	ctxIdx, _ := strconv.Atoi(fmt.Sprintf("%0"+idc.ctxDigits()+"d", idc.context))
	if ctxIdx != idc.context {
		panic("System ID does not belong to this context")
	}
	sid, _ := strconv.Atoi(vids[len(idc.ctxDigits()):])

	return sid
}

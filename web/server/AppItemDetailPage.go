package server

import (
	"context"
	"log"
	"net/http"

	protos "github.com/panyam/apptemplate/gen/go/apptemplate/v1"
)

type AppItemDetailPage struct {
	BasePage
	Header  Header
	AppItem *protos.AppItem
	AppItemId string
}

func (p *AppItemDetailPage) Load(r *http.Request, w http.ResponseWriter, vc *ViewContext) (err error, finished bool) {
	p.AppItemId = r.PathValue("appItemId")
	if p.AppItemId == "" {
		http.Error(w, "AppItem ID is required", http.StatusBadRequest)
		return nil, true
	}

	p.Title = "AppItem Details"
	p.Header.Load(r, w, vc)

	// Fetch the AppItem using the client manager
	client, err := vc.ClientMgr.GetAppItemsSvcClient()
	if err != nil {
		log.Printf("Error getting AppItems client: %v", err)
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return nil, true
	}

	req := &protos.GetAppItemRequest{
		Id: p.AppItemId,
	}

	resp, err := client.GetAppItem(context.Background(), req)
	if err != nil {
		log.Printf("Error fetching AppItem %s: %v", p.AppItemId, err)
		http.Error(w, "AppItem not found", http.StatusNotFound)
		return nil, true
	}

	if resp.Appitem != nil {
		// Convert from AppItemProject to AppItem (assuming we need the basic info)
		p.AppItem = &protos.AppItem{
			Id:          resp.Appitem.Id,
			Name:        resp.Appitem.Name,
			Description: resp.Appitem.Description,
			CreatedAt:   resp.Appitem.CreatedAt,
			UpdatedAt:   resp.Appitem.UpdatedAt,
		}
		p.Title = p.AppItem.Name
	}

	return nil, false
}

func (p *AppItemDetailPage) Copy() View { 
	return &AppItemDetailPage{} 
}
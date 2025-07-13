package server

import (
	"encoding/json"
	"net/http"
)

// AppItemsHandler handles appitem showcase pages
type AppItemsHandler struct {
	VC *ViewContext
}

// NewAppItemsHandler creates a new appitems handler
func NewAppItemsHandler(vc *ViewContext) *AppItemsHandler {
	return &AppItemsHandler{VC: vc}
}

// Handler returns an HTTP handler for appitems routes
func (h *AppItemsHandler) Handler() http.Handler {
	mux := http.NewServeMux()

	// AppItem listing page
	mux.HandleFunc("/appitems", h.handleAppItemListing)
	mux.HandleFunc("/appitems/", h.handleAppItemListing)

	// AppItem details page
	mux.HandleFunc("/appitem/", h.handleAppItemDetails)

	return mux
}

// handleAppItemListing renders the appitem listing page
func (h *AppItemsHandler) handleAppItemListing(w http.ResponseWriter, r *http.Request) {
	/*
		// Get all appitems from catalog
		appitems := h.catalog.ListAppItems()

		// Prepare template data
		data := map[string]any{
			"Title":    "AppItem Examples",
			"PageType": "appitem-listing",
			"AppItems": appitems,
			"PageDataJSON": toJSON(map[string]any{
				"pageType": "appitem-listing",
			}),
		}

		// Load and render template
		templates := h.templateGroup.MustLoad("appitems/listing.html", "")

		// Render the template
		if err := h.templateGroup.RenderHtmlTemplate(w, templates[0], "", data, nil); err != nil {
			http.Error(w, fmt.Sprintf("Failed to render page: %v", err), http.StatusInternalServerError)
			return
		}
	*/
}

// handleAppItemDetails renders the appitem details page
func (h *AppItemsHandler) handleAppItemDetails(w http.ResponseWriter, r *http.Request) {
	/*
		// Extract appitem ID from path
		// Path format: /appitem/bitly
		parts := strings.Split(r.URL.Path, "/")
		if len(parts) < 3 {
			http.NotFound(w, r)
			return
		}
		appitemID := parts[2]

		// Get appitem from catalog
		appitem := h.catalog.GetAppItem(appitemID)
		if appitem == nil {
			http.NotFound(w, r)
			return
		}

		// Get mode from query params (default to server mode)
		mode := "server"
		if r.URL.Query().Get("mode") == "wasm" {
			mode = "wasm"
		}

		// Get version (default to appitem's default version)
		version := r.URL.Query().Get("version")
		if version == "" {
			version = appitem.DefaultVersion
		}

		// Get SDL and recipe content for the version
		versionData := appitem.Versions[version]

		// Prepare minimal page data for the client (content will be loaded via API)
		pageData := map[string]any{
			"appitemId": appitem.ID,
			"mode":      mode,
		}

		// Prepare template data
		data := map[string]any{
			"Title":        appitem.Name + " - SDL AppItem",
			"PageType":     "appitem-details",
			"AppItem":      appitem,
			"Mode":         mode,
			"PageDataJSON": toJSON(pageData),
		}

		// Load and render template
		templates := h.templateGroup.MustLoad("appitems/details.html", "")

		// Render the template
		if err := h.templateGroup.RenderHtmlTemplate(w, templates[0], "", data, nil); err != nil {
			http.Error(w, fmt.Sprintf("Failed to render page: %v", err), http.StatusInternalServerError)
			return
		}
	*/
}

// toJSON converts data to JSON string for template use
func toJSON(v any) string {
	b, _ := json.Marshal(v)
	return string(b)
}

package services

import (
	"context"

	v1 "github.com/panyam/apptemplate/gen/go/apptemplate/v1"
)

// AppItemsServiceImpl implements the AppItemsService gRPC interface
type AppItemsServiceImpl struct {
}

// NewAppItemsService creates a new AppItemsService implementation
func NewAppItemsService() *AppItemsServiceImpl {
	return &AppItemsServiceImpl{}
}

// ListAppItems returns all available appitems
func (s *AppItemsServiceImpl) ListAppItems(ctx context.Context, req *v1.ListAppItemsRequest) (resp *v1.ListAppItemsResponse, err error) {
	resp = &v1.ListAppItemsResponse{}
	return
}

// GetAppItem returns a specific appitem with metadata
func (s *AppItemsServiceImpl) GetAppItem(ctx context.Context, req *v1.GetAppItemRequest) (resp *v1.GetAppItemResponse, err error) {
	resp = &v1.GetAppItemResponse{}
	return
}

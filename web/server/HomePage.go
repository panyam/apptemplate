package server

import (
	"net/http"
)

type HomePage struct {
	Header Header

	// Add any other components here to reflect what you want to show in your home page
	// Note that you would also update your HomePage templates to reflect these
}

func (p *HomePage) Load(r *http.Request, w http.ResponseWriter, vc *ViewContext) (err error, finished bool) {
	p.Header.Load(r, w, vc)
	return
}

type PrivacyPolicy struct {
	Header Header
}

func (p *PrivacyPolicy) Load(r *http.Request, w http.ResponseWriter, vc *ViewContext) (err error, finished bool) {
	return p.Header.Load(r, w, vc)
}

type TermsOfService struct {
	Header Header
}

func (p *TermsOfService) Load(r *http.Request, w http.ResponseWriter, vc *ViewContext) (err error, finished bool) {
	return p.Header.Load(r, w, vc)
}

func (g *TermsOfService) Copy() View { return &TermsOfService{} }
func (g *PrivacyPolicy) Copy() View  { return &PrivacyPolicy{} }
func (g *HomePage) Copy() View       { return &HomePage{} }

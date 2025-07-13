package server

import (
	"context"
	"fmt"
	"html/template"
	"io"
	"log"
	"net/http"
	"reflect"
	"strings"

	svc "github.com/panyam/apptemplate/services"
	gotl "github.com/panyam/goutils/template"
	oa "github.com/panyam/oneauth"
	tmplr "github.com/panyam/templar"
)

const TEMPLATES_FOLDER = "./web/templates"

type ViewContext struct {
	AuthMiddleware *oa.Middleware
	ClientMgr      *svc.ClientMgr
	Ctx            context.Context
	Templates      *tmplr.TemplateGroup
}

type ViewMaker func() View

type Copyable interface {
	Copy() View
}

func Copier[V Copyable](v V) ViewMaker {
	return v.Copy
}

type View interface {
	Load(r *http.Request, w http.ResponseWriter, vc *ViewContext) (err error, finished bool)
}

type RootViewsHandler struct {
	mux     *http.ServeMux
	Context *ViewContext
}

func NewRootViewsHandler(middleware *oa.Middleware, clients *svc.ClientMgr) *RootViewsHandler {
	out := RootViewsHandler{
		mux: http.NewServeMux(),
	}

	templates := tmplr.NewTemplateGroup()
	templates.Loader = (&tmplr.LoaderList{}).AddLoader(tmplr.NewFileSystemLoader(TEMPLATES_FOLDER))
	templates.AddFuncs(gotl.DefaultFuncMap())
	templates.AddFuncs(template.FuncMap{
		"Ctx": func() *ViewContext {
			return out.Context
		},
		"UserInfo": func(userId string) map[string]any {
			// Just a hacky cache
			return map[string]any{
				"FullName":  "XXXX YYY",
				"Name":      "XXXX",
				"AvatarUrl": "/avatar/url",
			}
		},
		"AsHtmlAttribs": func(m map[string]string) template.HTML {
			return `a = 'b' c = 'd'`
		},
		"Indented": func(nspaces int, code string) (formatted string) {
			lines := (strings.Split(strings.TrimSpace(code), "\n"))
			return strings.Join(lines, "<br/>")
		},
	})
	out.Context = &ViewContext{
		AuthMiddleware: middleware,
		ClientMgr:      clients,
		Templates:      templates,
	}

	// setup routes
	out.setupRoutes()
	return &out
}

func (b *RootViewsHandler) ViewRenderer(view ViewMaker, template string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		b.RenderView(view(), template, r, w)
	}
}

func (b *RootViewsHandler) RenderView(view View, template string, r *http.Request, w http.ResponseWriter) {
	if template == "" {
		t := reflect.TypeOf(view)
		e := t.Elem()
		template = e.Name()
	}
	err, finished := view.Load(r, w, b.Context)
	if !finished {
		if err != nil {
			log.Println("Error: ", err)
			fmt.Fprint(w, "Error rendering: ", err.Error())
		} else {
			tmpl, err := b.Context.Templates.Loader.Load(template, "")
			if err != nil {
				log.Println("Template Load Error: ", template, err)
				fmt.Fprint(w, "Error rendering: ", err.Error())
			} else {
				b.Context.Templates.RenderHtmlTemplate(w, tmpl[0], template, view, nil)
			}
		}
	}
}

func (b *RootViewsHandler) HandleError(err error, w io.Writer) {
	if err != nil {
		fmt.Fprint(w, "Error rendering: ", err.Error())
	}
}

func (n *RootViewsHandler) Handler() http.Handler {
	return n.mux
}

// Here you can setup all your view routes, pages, etc
func (n *RootViewsHandler) setupRoutes() {
	// This is the chance to setup all your routes for your app across various resources etc
	// Typically "/views" is dedicated for returning view fragments - eg via htmx
	n.mux.Handle("/views/", http.StripPrefix("/views", n.setupViewsMux()))

	// Then seutp your "resource" specific endpoints
	n.mux.Handle("/appitems/", http.StripPrefix("/appitems", n.setupAppItemsMux()))

	n.mux.HandleFunc("/about", n.ViewRenderer(Copier(&GenericPage{}), "AboutPage"))
	n.mux.HandleFunc("/contact", n.ViewRenderer(Copier(&GenericPage{}), "ContactUsPage"))
	n.mux.HandleFunc("/login", n.ViewRenderer(Copier(&LoginPage{}), ""))
	// n.mux.HandleFunc("/logout", n.onLogout)
	n.mux.HandleFunc("/privacy-policy", n.ViewRenderer(Copier(&PrivacyPolicy{}), ""))
	n.mux.HandleFunc("/terms-of-service", n.ViewRenderer(Copier(&TermsOfService{}), ""))
	n.mux.HandleFunc("/", n.ViewRenderer(Copier(&HomePage{}), ""))
	n.mux.Handle("/{invalidbits}/", http.NotFoundHandler()) // <-- Default 404

	// Alternatively if you have things getting built in a dist folder we could do:
	/*
		r.HandleFunc("/", func(w http.ResponseWriter, req *http.Request) {
			if req.URL.Path == "/" {
				http.Redirect(w, req, "/appitems", http.StatusFound)
				return
			}
			// Serve static files for other root-level paths
			http.FileServer(http.Dir(DIST_FOLDER)).ServeHTTP(w, req)
		})
	*/
}

func (n *RootViewsHandler) setupViewsMux() *http.ServeMux {
	mux := http.NewServeMux()

	// Setup the various views you want to return here
	/*, eg:
	mux.HandleFunc("/ComposerSelectionModal", n.ViewRenderer(Copier(&ComposerSelectionModal{}), ""))
	mux.HandleFunc("/ListTemplatesView", n.ViewRenderer(Copier(&ListTemplatesView{}), ""))
	mux.HandleFunc("/notations/ListView", n.ViewRenderer(Copier(&NotationListView{}), ""))
	*/

	// n.HandleView(Copier(&components.SelectTemplatePage{}), r, w)
	return mux
}

func (n *RootViewsHandler) setupAppItemsMux() *http.ServeMux {
	mux := http.NewServeMux()

	// here we ahve specific pages we go to for this resource
	/*
		mux.HandleFunc("/new", n.ViewRenderer(Copier(&ComposerPage{}), ""))
		mux.HandleFunc("/{notationId}/view", n.ViewRenderer(Copier(&NotationViewerPage{}), ""))

		mux.HandleFunc("/{notationId}/compose", n.ViewRenderer(Copier(&ComposerPage{}), ""))
		mux.HandleFunc("/{notationId}/copy", func(w http.ResponseWriter, r *http.Request) {
			notationId := r.PathValue("notationId")
			http.Redirect(w, r, fmt.Sprintf("/notations/new?copyFrom=%s", notationId), http.StatusFound)
		}) // .Methods("GET")
		mux.HandleFunc("/{notationId}", func(w http.ResponseWriter, r *http.Request) {
			log.Println("=============")
			log.Println("Catch all - should not be coming here", r.Header)
			log.Println("=============")
			http.Redirect(w, r, "/", http.StatusFound)
		}) // .Methods("DELETE")
	*/
	return mux
}

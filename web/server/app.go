package server

import (
	"log"
	"net/http"

	"github.com/alexedwards/scs/v2"
	"github.com/panyam/apptemplate/services"
	svc "github.com/panyam/apptemplate/services"
	oa "github.com/panyam/oneauth"
	oa2 "github.com/panyam/oneauth/oauth2"
	"github.com/panyam/templar"
)

// You may have a builder/bundler creating an output folder.  Set that path here.  It can be absolute or relative to
// where the executable will be running from
const DIST_FOLDER = "./web/dist"

// You can all this anything - but App is just a convention for all "top level" routes and handlers
type App struct {
	Api       *ApiHandler
	Auth      *oa.OneAuth         // One auth gives us alots of things out of the box
	Session   *scs.SessionManager // Session and auth go together
	ClientMgr *svc.ClientMgr

	// each reosurce can have its own dedicate page handler
	// we could have a dedicatd "views" handler and have them register it all or do it here
	// doing it here is one less level of indirection
	ViewsRoot *RootViewsHandler

	mux     *http.ServeMux
	BaseUrl string
}

func NewApp(ClientMgr *services.ClientMgr) (app *App, err error) {
	session := scs.New() //scs.NewCookieManager("u46IpCV9y5Vlur8YvODJEhgOY8m9JVE4"),
	// session.Store = NewMemoryStore(0)

	oneauth := oa.New("AppTemplate")
	oneauth.Session = session
	oneauth.Middleware.SessionGetter = func(r *http.Request, key string) any {
		return session.GetString(r.Context(), key)
	}
	oneauth.AddAuth("/google", oa2.NewGoogleOAuth2("", "", "", oneauth.SaveUserAndRedirect).Handler())
	oneauth.AddAuth("/github", oa2.NewGithubOAuth2("", "", "", oneauth.SaveUserAndRedirect).Handler())

	app = &App{
		//ClientMgr: ClientMgr,
		Session:   session,
		Auth:      oneauth,
		Api:       NewApiHandler(&oneauth.Middleware, ClientMgr),
		ViewsRoot: NewRootViewsHandler(&oneauth.Middleware, ClientMgr),
	}
	oneauth.AddAuth("/login", &oa.LocalAuth{
		UsernameField:            "email",
		ValidateUsernamePassword: app.ValidateUsernamePassword,
		HandleUser:               oneauth.SaveUserAndRedirect,
	})

	// TODO - setup oneauth.UserStore
	oneauth.UserStore = app

	// TODO - use godotenv and move configs to .env files instead
	/*
		if os.Getenv("APPTEMPLATE_ENV") == "dev" {
			n.authConfigs = DEV_CONFIGS
		}
	*/
	return
}

// GetRouter returns a configured HTTP router with all Canvas API routes
func (a *App) Handler() http.Handler {
	r := http.NewServeMux()

	// here is where we go and setup all the routes for the various prefixes

	// API routes
	r.Handle("/api/", http.StripPrefix("/api", a.Api.Handler()))

	// Fileappitem API endpoints
	// Serve examples directory for WASM demos
	r.Handle("/examples/", http.StripPrefix("/examples", http.FileServer(http.Dir("./examples/"))))

	r.Handle("/", a.ViewsRoot.Handler())

	return r
}

// SetupTemplates initializes the Templar template group
func SetupTemplates(templatesDir string) (*templar.TemplateGroup, error) {
	// Create a new template group
	group := templar.NewTemplateGroup()

	// Set up the file appitem loader with multiple paths
	group.Loader = templar.NewFileSystemLoader(
		templatesDir,
		templatesDir+"/shared",
		templatesDir+"/components",
	)

	// Preload common templates to ensure they're available
	commonTemplates := []string{
		"base.html",
		"appitems/listing.html",
		"appitems/details.html",
	}

	for _, tmpl := range commonTemplates {
		// Use defer to catch panics from MustLoad
		func() {
			defer func() {
				if r := recover(); r != nil {
					log.Printf("Template not found (will create): %s", tmpl)
				}
			}()
			group.MustLoad(tmpl, "")
		}()
	}

	return group, nil
}

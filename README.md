A minimal template app for go backends that require:

1. Protos/GRPC services
2. API Fronted by a gateway service
3. Powered by OneAuth for oauth
4. Basic frontend based on Templar go-templates - this can be customized in the future.
5. Tailwind for styling and Typescript for front end.  Add react/vue etc if youd like
6. Webpack for complex pages
7. Many sample page templates, eg ListPages, BorderLayout pages, pagse with DockView etc you can easily copy for other
   parts of your page.

Other backend choices (like datastores) are upto the app/service dev, eg:

1. Which services are to be added.
2. Which backends are to be used (for storage, etc)
3. How to deploy them to specific hosting providers (eg appengine, heroku etc)
4. Selecting frontend frameworks.

## Requirements

1. Basic/Standard Go Tooling:

* Go
* Air (for fast reloads)
* Protobuf
* GRPC
* Buf (for generating artificates from grpc protos)
* Webpack for any complex pages

## Getting Started

1. Clone this Repo

Replace the following variables:

Global Search and Replace:
==========================

AppTemplate -> Your backend name, eg "MyFancyGame"
apptemplate -> module name for your backend, age "myfancygame"
AppItem -> This is one of the entities in our proto, you can add more or replace this with the name of your key entity.  Feel free to add more entities that make sense for your system
appitem -> "Variable" names for the AppItem type in the code

./services/appitems_service.go - Definition of your service for appitems.  You can one one file for each entity type

TODO:
1. Common docker compose manifests for packaging for development.
2. Optional k8s configs if needed in the future for testing against cluster deployments

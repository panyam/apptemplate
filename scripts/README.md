# AppTemplate Drop-in Scripts

This directory contains scripts to help you drop AppTemplate components into existing projects and generate code for custom entities.

## Quick Start

```bash
# Basic usage - drop AppTemplate into current directory with Book and Author entities
./scripts/dropin /path/to/apptemplate . --entities Book,Author

# Full example with custom project settings
./scripts/dropin /path/to/apptemplate /path/to/target --entities Book,Library,Author \
  --project-name bookstore \
  --module-path github.com/mycompany/bookstore

# Dry run to see what would happen without making changes
./scripts/dropin /path/to/apptemplate . --entities Product,Category --dry-run
```

## What It Does

The `dropin` script:

1. **Copies Infrastructure**: Copies core AppTemplate files (utils, auth, web server, frontend build configs)
2. **Generates Entities**: Creates protobuf, Go services, web handlers, and templates for each entity
3. **Updates Configuration**: Modifies go.mod, package.json, and other config files
4. **Excludes AppItem**: Removes original AppItem files to avoid conflicts
5. **Runs Code Generation**: Executes `buf generate` and frontend builds

## Command Line Options

- `--entities`: **Required** - Comma-separated list of entities (e.g., `Book,Library,Author`)
- `--project-name`: Project name (default: target directory name)
- `--module-path`: Go module path (default: `github.com/$USER/projectname`)
- `--exclude-appitem`: Exclude AppItem files (default: true)
- `--dry-run`: Show what would be done without executing

## File Generation

For each entity (e.g., `Book`), the script generates:

### Protobuf Files
- `protos/[project]/v1/books.proto` - Service definitions and messages

### Go Service Layer  
- `services/books_service.go` - Business logic and CRUD operations
- Updates `services/clientmgr.go` to include Book client

### Web Server Components
- `web/server/BookDetailPage.go` - Detail page handler
- `web/server/BookListView.go` - List view component  
- `web/server/books_handler.go` - HTTP handlers
- Updates `web/server/views.go` with routes

### Templates
- `web/templates/BookDetailPage.html` - Detail page template
- `web/templates/BookList.html` - List view template

### Frontend Components
- `web/frontend/components/BookDetailsPage.ts` - TypeScript component

## Project Structure After Drop-in

```
target-project/
├── protos/
│   └── projectname/
│       └── v1/
│           ├── books.proto
│           ├── libraries.proto
│           └── authors.proto
├── services/
│   ├── books_service.go
│   ├── libraries_service.go
│   ├── authors_service.go
│   ├── auth.go
│   ├── grpcserver.go
│   └── clientmgr.go
├── web/
│   ├── server/
│   │   ├── BookDetailPage.go
│   │   ├── BookListView.go
│   │   ├── books_handler.go
│   │   └── ... (infrastructure files)
│   ├── templates/
│   │   ├── BookDetailPage.html
│   │   ├── BookList.html
│   │   └── ... (base templates)
│   └── frontend/
│       └── components/
│           ├── BookDetailsPage.ts
│           └── ... (infrastructure)
├── utils/
├── go.mod
├── main.go
└── Makefile
```

## Entity Naming Conventions

The script automatically handles naming transformations:

- `Book` → `BookDetailPage.go`, `BookListView.go`
- `book` → `books.proto`, `books_service.go`  
- `books` → Service names, route paths
- `Books` → Struct names in templates

Special pluralization handling:
- `Library` → `Libraries` (not `Librarys`)
- `Category` → `Categories`
- `Company` → `Companies`

## Requirements

- Python 3.6+
- `buf` CLI tool (for protobuf generation)
- Go 1.19+ (for the generated project)
- Node.js (for frontend builds)

## Examples

### E-commerce Store
```bash
./scripts/dropin . ../ecommerce --entities Product,Category,Order \
  --project-name ecommerce \
  --module-path github.com/mycompany/ecommerce
```

### Library Management
```bash 
./scripts/dropin . . --entities Book,Library,Author,Member \
  --project-name library-system
```

### Blog Platform
```bash
./scripts/dropin /path/to/apptemplate ../blog --entities Post,Category,User \
  --project-name blog \
  --module-path github.com/myblog/api
```

## Troubleshooting

### Missing Dependencies
If code generation fails, ensure you have:
```bash
# Install buf
brew install bufbuild/buf/buf

# Install frontend dependencies
cd web && npm install
```

### Module Path Issues
Update import statements if you change the module path after generation:
```bash
# Find and replace import paths
find . -name "*.go" -exec sed -i 's|old-module-path|new-module-path|g' {} \;
```

### Generated Code Conflicts
If you have existing entities, use different names or manually merge the generated code.

## Advanced Usage

### Custom Entity Properties
After generation, modify the protobuf files to add entity-specific fields:

```protobuf
// In protos/project/v1/books.proto
message Book {
  string id = 1;
  string title = 2;       // Add book-specific fields
  string author = 3;
  string isbn = 4;
  int32 pages = 5;
}
```

Then run `buf generate` to regenerate the Go/TypeScript code.

### Adding Business Logic
Customize the generated service files with entity-specific validation and business rules:

```go
// In services/books_service.go
func (s *BooksServiceImpl) validateBook(book *pb.Book) error {
    if book.Isbn == "" {
        return errors.New("ISBN is required")
    }
    // Add more validation...
}
```
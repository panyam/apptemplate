#!/usr/bin/env python3
"""
AppTemplate Drop-in Script

Copies AppTemplate components into existing projects and generates 
code for custom entities while excluding the original AppItem entity.

Usage:
    dropin <source_apptemplate_folder> <target_folder> --entities Entity1,Entity2,Entity3 [options]

Example:
    dropin /path/to/apptemplate . --entities Book,Library,Author --project-name bookstore
"""

import os
import sys
import argparse
import shutil
import re
import json
import yaml
from pathlib import Path
from typing import List, Dict, Set, Tuple
import subprocess

class AppTemplateDropin:
    def __init__(self, source_dir: str, target_dir: str, entities: List[str], **options):
        self.source_dir = Path(source_dir).resolve()
        self.target_dir = Path(target_dir).resolve()
        self.entities = entities
        self.project_name = options.get('project_name') or self.target_dir.name
        self.module_path = options.get('module_path') or f'github.com/{os.getenv("USER", "user")}/{self.project_name}'
        self.exclude_appitem = options.get('exclude_appitem', True)
        self.dry_run = options.get('dry_run', False)
        
        # Load configuration from config file
        self.config = self.load_config()
        
        # File patterns that contain entity references
        self.entity_patterns = {
            'AppItem': 'AppItem',
            'appitem': 'appitem', 
            'appitems': 'appitems',
            'AppItems': 'AppItems',
        }
        

    def run(self):
        """Main execution method"""
        print(f"🚀 AppTemplate Drop-in")
        print(f"📁 Source: {self.source_dir}")
        print(f"📁 Target: {self.target_dir}")
        print(f"🎯 Entities: {', '.join(self.entities)}")
        print(f"📦 Project: {self.project_name}")
        print(f"🔗 Module: {self.module_path}")
        
        if self.dry_run:
            print("🧪 DRY RUN MODE - No files will be modified")
        
        try:
            self.validate_directories()
            self.backup_target()
            self.copy_infrastructure()
            self.generate_entities()
            self.update_project_configuration()
            self.generate_code()
            print("✅ Drop-in completed successfully!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    def load_config(self):
        """Load configuration from dropin_config.yaml"""
        config_path = Path(__file__).parent / 'dropin_config.yaml'
        if not config_path.exists():
            # Fallback to minimal config if file doesn't exist
            return {
                'exclude_globs': ['gen/', 'gen/**', 'node_modules/', 'node_modules/**', '.git/', '.git/**'],
                'exclude_appitem_globs': []
            }
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def validate_directories(self):
        """Validate source and target directories"""
        if not self.source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {self.source_dir}")
            
        if not (self.source_dir / 'protos').exists():
            raise FileNotFoundError(f"Not a valid AppTemplate directory: {self.source_dir}")
            
        self.target_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"✅ Validated directories")

    def backup_target(self):
        """Create backup of target directory"""
        if self.dry_run:
            print("🧪 Would create backup")
            return
            
        backup_dir = self.target_dir.parent / f"{self.target_dir.name}.backup"
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        
        if list(self.target_dir.iterdir()):  # If target has files
            shutil.copytree(self.target_dir, backup_dir)
            print(f"💾 Created backup at {backup_dir}")

    def copy_infrastructure(self):
        """Copy all files except those excluded, using opt-out approach"""
        print("📋 Copying infrastructure files...")
        
        def copy_recursive(src_path: Path, dst_path: Path, rel_path: str = ""):
            """Recursively copy files, excluding based on config"""
            if src_path.is_dir():
                # Check if directory should be excluded
                if self.should_exclude_path(rel_path):
                    return
                    
                if dst_path.exists():
                    if dst_path.is_file():
                        dst_path.unlink()
                else:
                    dst_path.mkdir(parents=True, exist_ok=True)
                
                for item in src_path.iterdir():
                    item_rel_path = f"{rel_path}/{item.name}" if rel_path else item.name
                    copy_recursive(item, dst_path / item.name, item_rel_path)
            else:
                # Check if file should be excluded
                if self.should_exclude_path(rel_path):
                    return
                
                if self.dry_run:
                    print(f"🧪 Would copy: {rel_path}")
                    return
                
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy and transform file
                if self.should_transform_file(src_path):
                    content = src_path.read_text(encoding='utf-8', errors='ignore')
                    content = self.transform_project_content(content)
                    dst_path.write_text(content, encoding='utf-8')
                else:
                    shutil.copy2(src_path, dst_path)
                print(f"📄 Copied: {rel_path}")
        
        # Start recursive copy from source directory
        copy_recursive(self.source_dir, self.target_dir)

    def should_exclude_path(self, rel_path: str) -> bool:
        """Check if a path should be excluded based on config"""
        import fnmatch
        
        # Don't exclude the root directory (empty path)
        if not rel_path:
            return False
            
        # Always exclude hidden files/dirs except .devloop.yaml
        if rel_path.startswith('.') and rel_path != '.devloop.yaml':
            return True
        
        # Check global exclude patterns
        for pattern in self.config.get('exclude_globs', []):
            if fnmatch.fnmatch(rel_path, pattern):
                return True
        
        # Check AppItem-specific exclusions when exclude_appitem is True
        if self.exclude_appitem:
            for pattern in self.config.get('exclude_appitem_globs', []):
                if fnmatch.fnmatch(rel_path, pattern):
                    return True
        
        return False

    def transform_directory(self, directory_path: Path):
        """Transform all transformable files in a directory recursively"""
        for file_path in directory_path.rglob('*'):
            if file_path.is_file() and self.should_transform_file(file_path):
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    content = self.transform_project_content(content)
                    file_path.write_text(content, encoding='utf-8')
                except Exception as e:
                    print(f"⚠️  Failed to transform {file_path}: {e}")

    def should_transform_file(self, file_path: Path) -> bool:
        """Determine if a file should be transformed (text files only)"""
        # Transform text-based files
        text_extensions = {'.go', '.js', '.ts', '.json', '.html', '.css', '.md', '.yaml', '.yml', '.proto', '.txt'}
        return file_path.suffix.lower() in text_extensions or file_path.name in {'Makefile', '.devloop.yaml'}

    def transform_project_content(self, content: str) -> str:
        """Transform content by replacing project-wide references"""
        # 1. Module path transformations
        content = self.transform_import_paths(content)
        
        # 2. Project name transformations
        project_lower = self.project_name.lower()
        project_upper = self.project_name.upper()
        
        transformations = {
            # Environment variables
            'APPTEMPLATE_': f'{project_upper}_',
            
            # Binary/executable names
            '/tmp/apptemplate': f'/tmp/{project_lower}',
            
            # Proto package names and imports
            'package apptemplate.v1': f'package {project_lower}.v1',
            'import "apptemplate/v1/': f'import "{project_lower}/v1/',
            '/gen/go/apptemplate/': f'/gen/go/{project_lower}/',
            
            # Proto content references
            'apptemplate_content': f'{project_lower}_content',
            
            # App identifiers
            'APP_ID = "apptemplate"': f'APP_ID = "{project_lower}"',
            
            # OneAuth app names
            'oa.New("AppTemplate")': f'oa.New("{self.project_name}")',
            
            # HTML titles and content
            'Welcome to AppTemplate': f'Welcome to {self.project_name}',
            'AppTemplate - ': f'{self.project_name} - ',
            
            # Package.json fields
            '"apptemplate"': f'"{project_lower}"',
            'panyam/apptemplate': f'panyam/{project_lower}',  # GitHub URLs
            
            # Webpack library names
            'library: ["apptemplate"': f'library: ["{project_lower}"',
            
            # README content
            'AppTemplate ->': f'{self.project_name} ->',
            'apptemplate ->': f'{project_lower} ->',
        }
        
        for old, new in transformations.items():
            content = content.replace(old, new)
            
        return content


    def generate_entities(self):
        """Generate files for each entity"""
        print("🏗️  Generating entity files...")
        
        # First copy the models.proto file
        self.copy_models_proto()
        
        for entity in self.entities:
            print(f"🎯 Generating files for entity: {entity}")
            self.generate_proto_files(entity)
            self.generate_service_files(entity)
            self.generate_web_files(entity)
            self.generate_frontend_files(entity)

    def copy_models_proto(self):
        """Copy and update models.proto file"""
        source_models = self.source_dir / 'protos/apptemplate/v1/models.proto'
        if not source_models.exists():
            return
            
        target_models = self.target_dir / f'protos/{self.project_name.lower()}/v1/models.proto'
        
        if self.dry_run:
            print(f"🧪 Would copy: models.proto")
            return
            
        target_models.parent.mkdir(parents=True, exist_ok=True)
        
        content = source_models.read_text()
        content = self.transform_project_content(content)
        
        # Replace AppItem with entity definitions if not excluding appitem
        if not self.exclude_appitem:
            # Keep the AppItem as-is
            pass
        else:
            # Remove AppItem and add entity definitions
            content = self.remove_appitem_and_add_entities(content)
        
        target_models.write_text(content)
        print(f"📄 Generated: models.proto")

    def remove_appitem_and_add_entities(self, content: str) -> str:
        """Remove AppItem definition and add entity definitions"""
        # Remove the AppItem message definition
        lines = content.split('\n')
        filtered_lines = []
        in_appitem_message = False
        
        for line in lines:
            if line.startswith('message AppItem {'):
                in_appitem_message = True
                continue
            elif in_appitem_message and line == '}':
                in_appitem_message = False
                continue
            elif in_appitem_message:
                continue
            else:
                filtered_lines.append(line)
        
        # Add entity definitions
        entity_definitions = []
        for entity in self.entities:
            entity_def = f"""
message {entity} {{
  google.protobuf.Timestamp created_at = 1;
  google.protobuf.Timestamp updated_at = 2;

  // Unique ID for the {entity.lower()}
  string id = 3;

  // Name if items have names
  string name = 4;

  // Description if {entity.lower()} has a description
  string description = 5;

  // Some tags
  repeated string tags = 6;

  // A possible image url
  string image_url = 7;

  // Difficulty - example attribute
  string difficulty = 8;
}}"""
            entity_definitions.append(entity_def)
        
        # Join the content and add entity definitions
        result = '\n'.join(filtered_lines) + '\n' + '\n'.join(entity_definitions) + '\n'
        return result

    def generate_proto_files(self, entity: str):
        """Generate protobuf files for entity"""
        source_proto = self.source_dir / 'protos/apptemplate/v1/appitems.proto'
        if not source_proto.exists():
            print(f"⚠️  Source proto not found: {source_proto}")
            return
            
        entity_plural = self.pluralize(entity.lower())
        target_proto = self.target_dir / f'protos/{self.project_name.lower()}/v1/{entity_plural}.proto'
        
        if self.dry_run:
            print(f"🧪 Would generate: {target_proto}")
            return
            
        target_proto.parent.mkdir(parents=True, exist_ok=True)
        
        # Read and transform proto content
        content = source_proto.read_text()
        content = self.transform_entity_content(content, entity)
        content = self.transform_project_content(content)
        
        target_proto.write_text(content)
        print(f"📄 Generated: {target_proto}")

    def generate_service_files(self, entity: str):
        """Generate Go service files for entity"""
        source_service = self.source_dir / 'services/appitems_service.go'
        if not source_service.exists():
            print(f"⚠️  Source service not found: {source_service}")
            return
            
        entity_plural = self.pluralize(entity.lower())
        target_service = self.target_dir / f'services/{entity_plural}_service.go'
        
        if self.dry_run:
            print(f"🧪 Would generate: {target_service}")
            return
            
        target_service.parent.mkdir(parents=True, exist_ok=True)
        
        # Read and transform service content
        content = source_service.read_text()
        content = self.transform_entity_content(content, entity)
        content = self.transform_project_content(content)
        
        target_service.write_text(content)
        print(f"📄 Generated: {target_service}")

    def generate_web_files(self, entity: str):
        """Generate web server files for entity"""
        entity_plural = self.pluralize(entity.lower())
        web_files = [
            ('web/server/AppItemDetailPage.go', f'web/server/{entity}DetailPage.go'),
            ('web/server/AppItemListView.go', f'web/server/{entity}ListView.go'),
            ('web/server/appitems_handler.go', f'web/server/{entity_plural}_handler.go'),
            ('web/templates/AppItemDetailPage.html', f'web/templates/{entity}DetailPage.html'),
            ('web/templates/AppItemList.html', f'web/templates/{entity}List.html'),
        ]
        
        for source_file, target_file in web_files:
            source_path = self.source_dir / source_file
            if not source_path.exists():
                continue
                
            target_path = self.target_dir / target_file
            
            if self.dry_run:
                print(f"🧪 Would generate: {target_file}")
                continue
                
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            content = source_path.read_text()
            content = self.transform_entity_content(content, entity)
            content = self.transform_project_content(content)
            
            target_path.write_text(content)
            print(f"📄 Generated: {target_file}")

    def generate_frontend_files(self, entity: str):
        """Generate frontend TypeScript files for entity"""
        source_ts = self.source_dir / 'web/frontend/components/AppItemDetailsPage.ts'
        if not source_ts.exists():
            return
            
        target_ts = self.target_dir / f'web/frontend/components/{entity}DetailsPage.ts'
        
        if self.dry_run:
            print(f"🧪 Would generate: {target_ts}")
            return
            
        target_ts.parent.mkdir(parents=True, exist_ok=True)
        
        content = source_ts.read_text()
        content = self.transform_entity_content(content, entity)
        content = self.transform_project_content(content)
        
        target_ts.write_text(content)
        print(f"📄 Generated: {target_ts}")

    def transform_entity_content(self, content: str, entity: str) -> str:
        """Transform content by replacing AppItem references with entity name"""
        entity_lower = entity.lower()
        entity_plural = self.pluralize(entity_lower)
        entity_plural_title = self.pluralize(entity)
        
        transformations = {
            'AppItem': entity,
            'appitem': entity_lower,
            'appitems': entity_plural,
            'AppItems': entity_plural_title,
        }
        
        # Apply basic transformations first
        for old, new in transformations.items():
            content = content.replace(old, new)
        
        # Fix service name pluralization issues (e.g., LibrarysService -> LibrariesService)
        # This handles cases where the basic pluralization doesn't work correctly
        if entity_lower == 'library':
            content = content.replace('LibrarysService', 'LibrariesService')
            content = content.replace('librarysService', 'librariesService')
            content = content.replace('ListLibrarys', 'ListLibraries')
            content = content.replace('GetLibrarys', 'GetLibraries')
            content = content.replace('librarys:', 'libraries:')
            content = content.replace('/librarys', '/libraries')
            
        return content

    def transform_import_paths(self, content: str) -> str:
        """Transform Go import paths to use new module path"""
        old_import = 'github.com/panyam/apptemplate'
        return content.replace(old_import, self.module_path)

    def pluralize(self, word: str) -> str:
        """Simple pluralization logic"""
        # Special cases
        special_cases = {
            'library': 'libraries',
            'Library': 'Libraries',
            'category': 'categories', 
            'Category': 'Categories',
            'company': 'companies',
            'Company': 'Companies',
        }
        
        if word in special_cases:
            return special_cases[word]
            
        if word.endswith('y') and word[-2:-1] not in 'aeiou':
            return word[:-1] + 'ies'
        elif word.endswith(('s', 'sh', 'ch', 'x', 'z')):
            return word + 'es'
        else:
            return word + 's'

    def update_project_configuration(self):
        """Update project-wide configuration files"""
        print("⚙️  Updating project configuration...")
        
        self.update_go_mod()
        self.update_package_json()
        self.update_devloop_config()

    def update_go_mod(self):
        """Update go.mod with new module path"""
        go_mod_path = self.target_dir / 'go.mod'
        if not go_mod_path.exists():
            return
            
        if self.dry_run:
            print("🧪 Would update go.mod")
            return
            
        content = go_mod_path.read_text()
        content = re.sub(
            r'module github\.com/panyam/apptemplate',
            f'module {self.module_path}',
            content
        )
        go_mod_path.write_text(content)
        print("📄 Updated go.mod")

    def update_package_json(self):
        """Update package.json with project details"""
        package_json_path = self.target_dir / 'web/package.json'
        if not package_json_path.exists():
            return
            
        if self.dry_run:
            print("🧪 Would update package.json")
            return
            
        with open(package_json_path, 'r') as f:
            data = json.load(f)
            
        data['name'] = self.project_name
        data['description'] = f'{self.project_name} web frontend'
        
        with open(package_json_path, 'w') as f:
            json.dump(data, f, indent=2)
            
        print("📄 Updated package.json")

    def update_devloop_config(self):
        """Update .devloop.yaml if it exists"""
        devloop_path = self.target_dir / '.devloop.yaml'
        if not devloop_path.exists():
            return
            
        if self.dry_run:
            print("🧪 Would update .devloop.yaml")
            return
            
        content = devloop_path.read_text()
        content = content.replace('apptemplate', self.project_name)
        devloop_path.write_text(content)
        print("📄 Updated .devloop.yaml")

    def generate_code(self):
        """Run code generation commands"""
        print("🔧 Running code generation...")
        
        if self.dry_run:
            print("🧪 Would run: buf generate")
            print("🧪 Would run: make build-frontend")
            return
            
        # Run buf generate for protobuf code
        try:
            subprocess.run(['buf', 'generate'], cwd=self.target_dir, check=True)
            print("✅ Generated protobuf code")
        except subprocess.CalledProcessError:
            print("⚠️  Failed to run buf generate")
            
        # Run frontend build
        try:
            subprocess.run(['make', 'build-frontend'], cwd=self.target_dir / 'web', check=True)
            print("✅ Built frontend")
        except subprocess.CalledProcessError:
            print("⚠️  Failed to build frontend")


def auto_detect_source():
    """Auto-detect AppTemplate source directory from script location"""
    script_dir = Path(__file__).parent.resolve()
    # Script is in scripts/ subdirectory, so parent is AppTemplate root
    apptemplate_dir = script_dir.parent
    
    # Verify this looks like an AppTemplate directory
    if (apptemplate_dir / 'protos').exists() and (apptemplate_dir / 'web').exists():
        return str(apptemplate_dir)
    
    # Maybe script is copied elsewhere, try current directory
    current_dir = Path.cwd()
    if (current_dir / 'protos').exists() and (current_dir / 'web').exists():
        return str(current_dir)
        
    return None

def main():
    parser = argparse.ArgumentParser(
        description='AppTemplate Drop-in Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect source, drop into current directory
  dropin . --entities Book,Author
  
  # Specify source and target
  dropin /path/to/apptemplate /path/to/target --entities Book,Author
  
  # Full configuration
  dropin . ../new-project --entities Product,Category \\
    --project-name ecommerce --module-path github.com/company/ecommerce
        """
    )
    
    parser.add_argument('args', nargs='+', help='[source] target - Target directory (source auto-detected if not provided)')
    parser.add_argument('--entities', required=True, help='Comma-separated list of entities')
    parser.add_argument('--project-name', help='Project name (default: target directory name)')
    parser.add_argument('--module-path', help='Go module path')
    parser.add_argument('--exclude-appitem', action='store_true', default=True, help='Exclude AppItem files')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    
    args = parser.parse_args()
    
    # Handle positional arguments
    if len(args.args) == 1:
        # Only target provided - auto-detect source
        target = args.args[0]
        source = auto_detect_source()
        if not source:
            print("❌ Error: Could not auto-detect AppTemplate source directory.")
            print("   Please provide source directory explicitly:")
            print("   dropin /path/to/apptemplate /path/to/target --entities ...")
            sys.exit(1)
    elif len(args.args) == 2:
        # Both source and target provided
        source = args.args[0]
        target = args.args[1]
    else:
        parser.error("Provide either target directory (source auto-detected) or both source and target directories")
    
    entities = [e.strip() for e in args.entities.split(',')]
    
    dropin = AppTemplateDropin(
        source_dir=source,
        target_dir=target,
        entities=entities,
        project_name=args.project_name,
        module_path=args.module_path,
        exclude_appitem=args.exclude_appitem,
        dry_run=args.dry_run,
    )
    
    dropin.run()


if __name__ == '__main__':
    main()
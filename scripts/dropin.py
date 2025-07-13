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
from pathlib import Path
from typing import List, Dict, Set, Tuple
import subprocess

class AppTemplateDropin:
    def __init__(self, source_dir: str, target_dir: str, entities: List[str], **options):
        self.source_dir = Path(source_dir).resolve()
        self.target_dir = Path(target_dir).resolve()
        self.entities = entities
        self.project_name = options.get('project_name', self.target_dir.name)
        self.module_path = options.get('module_path') or f'github.com/{os.getenv("USER", "user")}/{self.project_name}'
        self.exclude_appitem = options.get('exclude_appitem', True)
        self.dry_run = options.get('dry_run', False)
        
        # File patterns that contain entity references
        self.entity_patterns = {
            'AppItem': 'AppItem',
            'appitem': 'appitem', 
            'appitems': 'appitems',
            'AppItems': 'AppItems',
        }
        
        # Files to exclude (AppItem specific)
        self.exclude_files = set([
            'services/appitems_service.go',
            'web/server/AppItemDetailPage.go', 
            'web/server/AppItemListView.go',
            'web/server/appitems_handler.go',
            'web/templates/AppItemDetailPage.html',
            'web/templates/AppItemList.html',
            'web/frontend/components/AppItemDetailsPage.ts',
            'protos/apptemplate/v1/appitems.proto',
        ]) if self.exclude_appitem else set()
        
        # Infrastructure files to copy as-is
        self.infrastructure_files = {
            'utils/',
            'services/auth.go',
            'services/grpcserver.go', 
            'services/clientmgr.go',
            'services/models.go',
            'web/server/webserver.go',
            'web/server/app.go',
            'web/server/views.go',
            'web/server/api.go',
            'web/server/connect.go',
            'web/server/connectbridge.go',
            'web/server/user.go',
            'web/server/GenericPage.go',
            'web/server/Header.go',
            'web/server/HomePage.go',
            'web/server/LoginPage.go',
            'web/server/Paginator.go',
            'web/frontend/css/',
            'web/static/',
            'web/package.json',
            'web/tailwind.config.js',
            'web/webpack.config.js',
            'web/tsconfig.json',
            'web/Makefile',
            'web/templates/BasePage.html',
            'web/templates/Header.html',
            'web/templates/HomePage.html',
            'web/templates/LoginPage.html',
            'web/templates/ModalContainer.html',
            'web/templates/ToastContainer.html',
            'web/templates/PrivacyPolicy.html',
            'Makefile',
            'buf.yaml',
            'buf.gen.yaml',
            'go.mod',
            'go.sum',
            'main.go',
            'lib/',
            'README.md',
            '.devloop.yaml',
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
        """Copy infrastructure files that don't need entity transformation"""
        print("📋 Copying infrastructure files...")
        
        for file_pattern in self.infrastructure_files:
            source_path = self.source_dir / file_pattern
            
            if not source_path.exists():
                continue
                
            target_path = self.target_dir / file_pattern
            
            if self.dry_run:
                print(f"🧪 Would copy: {file_pattern}")
                continue
                
            if source_path.is_dir():
                if target_path.exists():
                    shutil.rmtree(target_path)
                shutil.copytree(source_path, target_path)
            else:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, target_path)
                
            print(f"📄 Copied: {file_pattern}")

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
            
        target_models = self.target_dir / f'protos/{self.project_name}/v1/models.proto'
        
        if self.dry_run:
            print(f"🧪 Would copy: models.proto")
            return
            
        target_models.parent.mkdir(parents=True, exist_ok=True)
        
        content = source_models.read_text()
        content = content.replace('apptemplate', self.project_name)
        content = self.transform_import_paths(content)
        
        target_models.write_text(content)
        print(f"📄 Generated: models.proto")

    def generate_proto_files(self, entity: str):
        """Generate protobuf files for entity"""
        source_proto = self.source_dir / 'protos/apptemplate/v1/appitems.proto'
        if not source_proto.exists():
            print(f"⚠️  Source proto not found: {source_proto}")
            return
            
        entity_plural = self.pluralize(entity.lower())
        target_proto = self.target_dir / f'protos/{self.project_name}/v1/{entity_plural}.proto'
        
        if self.dry_run:
            print(f"🧪 Would generate: {target_proto}")
            return
            
        target_proto.parent.mkdir(parents=True, exist_ok=True)
        
        # Read and transform proto content
        content = source_proto.read_text()
        content = self.transform_entity_content(content, entity)
        content = content.replace('apptemplate', self.project_name)
        
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
        content = self.transform_import_paths(content)
        
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
            content = self.transform_import_paths(content)
            
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
        
        for old, new in transformations.items():
            content = content.replace(old, new)
            
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


def main():
    parser = argparse.ArgumentParser(description='AppTemplate Drop-in Script')
    parser.add_argument('source', help='Source AppTemplate directory')
    parser.add_argument('target', help='Target project directory')
    parser.add_argument('--entities', required=True, help='Comma-separated list of entities')
    parser.add_argument('--project-name', help='Project name (default: target directory name)')
    parser.add_argument('--module-path', help='Go module path')
    parser.add_argument('--exclude-appitem', action='store_true', default=True, help='Exclude AppItem files')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    
    args = parser.parse_args()
    
    entities = [e.strip() for e in args.entities.split(',')]
    
    dropin = AppTemplateDropin(
        source_dir=args.source,
        target_dir=args.target,
        entities=entities,
        project_name=args.project_name,
        module_path=args.module_path,
        exclude_appitem=args.exclude_appitem,
        dry_run=args.dry_run,
    )
    
    dropin.run()


if __name__ == '__main__':
    main()
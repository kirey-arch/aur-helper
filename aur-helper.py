#!/usr/bin/env python3

# Program name: AUR Helper
# Copyright (C) 2025 kirey-arch
# Liccensed under the GNU GPL v3. See LICENSE for more information

import subprocess
import shutil
import os
import sys
import json
import re
import tempfile
import time
from datetime import datetime
from difflib import get_close_matches
from pathlib import Path
from typing import List, Optional, Dict, Tuple


class Colors:
    """ANSI color codes || terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class Logger:
    
    def __init__(self, log_file: str = None):
        self.log_file = log_file or os.path.expanduser("~/.cache/aur-helper.log")
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def log(self, level: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry)
        except Exception:
            pass 
    
    def info(self, message: str):
        self.log("INFO", message)
    
    def error(self, message: str):
        self.log("ERROR", message)
    
    def warning(self, message: str):
        self.log("WARNING", message)


class Config:
    """management"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or os.path.expanduser("~/.config/aur-helper/config.json")
        self.default_config = {
            "default_manager": "pacman",
            "auto_confirm": False,
            "show_progress": True,
            "backup_before_operations": True,
            "max_search_results": 10,
            "search_cutoff": 0.3,
            "colors_enabled": True
        }
        self.config = self.load_config()
    
    def load_config(self) -> dict:
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    return {**self.default_config, **config}
        except Exception:
            pass
        return self.default_config.copy()
    
    def save_config(self):
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"{Colors.YELLOW}Warning: Could not save config: {e}{Colors.END}")
    
    def get(self, key: str, default=None):
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        self.config[key] = value
        self.save_config()


class ProgressIndicator:
    """progress indicator"""
    
    def __init__(self, message: str, enabled: bool = True):
        self.message = message
        self.enabled = enabled
        self.running = False
    
    def __enter__(self):
        if self.enabled:
            print(f"{Colors.BLUE}{self.message}...{Colors.END}", end="", flush=True)
            self.running = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.enabled and self.running:
            if exc_type is None:
                print(f" {Colors.GREEN}✓{Colors.END}")
            else:
                print(f" {Colors.RED}✗{Colors.END}")


class AURHelper:
    """main helper class"""
    
    def __init__(self):
        self.logger = Logger()
        self.config = Config()
        self.supported_managers = {
            "pacman": {"name": "Pacman", "needs_sudo": True, "aur_support": False},
            "yay": {"name": "Yay", "needs_sudo": False, "aur_support": True},
            "paru": {"name": "Paru", "needs_sudo": False, "aur_support": True}
        }
        self.current_manager = None
    
    def run_command(self, cmd: str, capture_output: bool = True, shell: bool = True) -> Tuple[bool, str]:
        """execute command with improved error handling"""
        self.logger.info(f"Executing command: {cmd}")
        
        try:
            if capture_output:
                result = subprocess.run(
                    cmd,
                    shell=shell,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=300  # 5 minutes
                )
                success = result.returncode == 0
                output = result.stdout.strip()
            else:
                result = subprocess.run(cmd, shell=shell, timeout=300)
                success = result.returncode == 0
                output = ""
            
            if not success:
                self.logger.error(f"Command failed: {cmd} (exit code: {result.returncode})")
                if capture_output:
                    self.logger.error(f"Output: {output}")
            
            return success, output
        
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out: {cmd}")
            return False, "Command timed out"
        except Exception as e:
            self.logger.error(f"Command execution failed: {cmd} - {str(e)}")
            return False, str(e)
    
    def is_installed(self, tool: str) -> bool:
        """is installed"""
        return shutil.which(tool) is not None
    
    def validate_package_name(self, package: str) -> bool:
        """name format"""
        # validation for Arch package names
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9@._+-]*$'
        return bool(re.match(pattern, package)) and len(package) <= 255
    
    def get_installed_packages(self) -> List[str]:
        """list of installed packages"""
        success, output = self.run_command("pacman -Qq")
        if success:
            return output.split('\n') if output else []
        return []
    
    def backup_system_state(self) -> Optional[str]:
        """backup of current package state"""
        if not self.config.get("backup_before_operations"):
            return None
        
        try:
            backup_dir = os.path.expanduser("~/.cache/aur-helper/backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"packages_{timestamp}.txt")
            
            success, output = self.run_command("pacman -Qq")
            if success:
                with open(backup_file, 'w') as f:
                    f.write(output)
                self.logger.info(f"System state backed up to: {backup_file}")
                return backup_file
        except Exception as e:
            self.logger.error(f"Failed to backup system state: {e}")
        
        return None
    
    def install_helper(self, helper: str) -> bool:
        print(f"{Colors.YELLOW}{helper} not found.{Colors.END}")
        
        if self.config.get("auto_confirm"):
            choice = "y"
        else:
            choice = input(f"Do you want to install {helper}? (y/n): ").lower().strip()
        
        if choice not in ['y', 'yes']:
            print(f"{Colors.BLUE}Installation cancelled.{Colors.END}")
            return False
        
        # git is available?
        if not self.is_installed("git"):
            print(f"{Colors.BLUE}Installing git dependency...{Colors.END}")
            success, _ = self.run_command("sudo pacman -Sy git --noconfirm", capture_output=False)
            if not success:
                print(f"{Colors.RED}Failed to install git. Cannot proceed.{Colors.END}")
                return False
        
        # temporary directory for building
        with tempfile.TemporaryDirectory() as temp_dir:
            old_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                
                with ProgressIndicator(f"Cloning {helper} repository", self.config.get("show_progress")):
                    success, _ = self.run_command(f"git clone https://aur.archlinux.org/{helper}.git")
                    if not success:
                        print(f"{Colors.RED}Failed to clone {helper} repository.{Colors.END}")
                        return False
                
                os.chdir(helper)
                
                with ProgressIndicator(f"Building and installing {helper}", self.config.get("show_progress")):
                    success, output = self.run_command("makepkg -si --noconfirm", capture_output=False)
                    if not success:
                        print(f"{Colors.RED}Failed to build/install {helper}.{Colors.END}")
                        return False
                
                print(f"{Colors.GREEN}✅ {helper} installed successfully!{Colors.END}")
                return True
                
            finally:
                os.chdir(old_cwd)
    
    def check_package_exists(self, manager: str, package: str) -> bool:
        """package exists in repositories?"""
        with ProgressIndicator(f"Checking if '{package}' exists", self.config.get("show_progress")):
            # search patterns for better accuracy
            patterns = [f"^{package}$", f"^{package} ", f"/{package} "]
            
            for pattern in patterns:
                success, output = self.run_command(f"{manager} -Ss '{pattern}'")
                if success and output:
                    lines = output.splitlines()
                    for line in lines:
                        # More precise matching
                        if f"/{package} " in line or line.strip().endswith(f"/{package}"):
                            return True
        return False
    
    def search_packages(self, manager: str, query: str) -> List[Dict[str, str]]:
        """search with detailed information"""
        success, output = self.run_command(f"{manager} -Ss {query}")
        if not success or not output:
            return []
        
        packages = []
        lines = output.splitlines()
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            if "/" in line and not line.startswith(" "):
                try:
                    # repo/name version
                    parts = line.split()
                    if len(parts) >= 2:
                        repo_package = parts[0]
                        version = parts[1] if len(parts) > 1 else "unknown"
                        
                        if "/" in repo_package:
                            repo, name = repo_package.split("/", 1)
                            
                            # description from next line if available
                            description = ""
                            if i + 1 < len(lines) and lines[i + 1].startswith(" "):
                                description = lines[i + 1].strip()
                            
                            packages.append({
                                "name": name,
                                "repo": repo,
                                "version": version,
                                "description": description
                            })
                except (IndexError, ValueError):
                    pass
            i += 1
        
        return packages
    
    def search_similar_interactive(self, manager: str, query: str) -> Optional[str]:
        """Enhanced interactive package search"""
        print(f"{Colors.BLUE}🔍 Searching for packages matching '{query}'...{Colors.END}")
        
        packages = self.search_packages(manager, query)
        if not packages:
            print(f"{Colors.YELLOW}No packages found.{Colors.END}")
            return None
        
        # remove duplicates and get fuzzy matches
        unique_names = list(dict.fromkeys([pkg["name"] for pkg in packages]))
        similar = get_close_matches(
            query, 
            unique_names, 
            n=self.config.get("max_search_results", 10),
            cutoff=self.config.get("search_cutoff", 0.3)
        )
        
        if not similar:
            print(f"{Colors.YELLOW}No similar packages found.{Colors.END}")
            return None
        
        # create package lookup for detailed info
        package_lookup = {pkg["name"]: pkg for pkg in packages}
        
        print(f"\n{Colors.GREEN}📦 Similar packages found:{Colors.END}")
        print(f"{Colors.CYAN}{'No.':<4} {'Name':<25} {'Repo':<10} {'Description'}{Colors.END}")
        print("-" * 80)
        
        for i, name in enumerate(similar):
            pkg = package_lookup.get(name, {"repo": "unknown", "description": ""})
            desc = pkg.get("description", "")[:40] + "..." if len(pkg.get("description", "")) > 40 else pkg.get("description", "")
            print(f"{Colors.WHITE}{i + 1:<4} {name:<25} {pkg.get('repo', 'unknown'):<10} {desc}{Colors.END}")
        
        try:
            choice = input(f"\n{Colors.YELLOW}Enter package number (0 to cancel): {Colors.END}").strip()
            if choice == "0" or choice.lower() == "cancel":
                print(f"{Colors.BLUE}Search cancelled.{Colors.END}")
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(similar):
                selected = similar[choice_num - 1]
                pkg_info = package_lookup.get(selected, {})
                print(f"\n{Colors.GREEN}Selected: {selected} ({pkg_info.get('repo', 'unknown')})")
                print(f"Description: {pkg_info.get('description', 'No description')}{Colors.END}")
                return selected
            else:
                print(f"{Colors.RED}Invalid selection.{Colors.END}")
                return None
        
        except ValueError:
            print(f"{Colors.RED}Invalid input. Please enter a number.{Colors.END}")
            return None
    
    def install_package(self, manager: str, package: str) -> bool:
        if not self.validate_package_name(package):
            print(f"{Colors.RED}Invalid package name: {package}{Colors.END}")
            return False
        
        # already installed?
        installed_packages = self.get_installed_packages()
        if package in installed_packages:
            print(f"{Colors.YELLOW}Package '{package}' is already installed.{Colors.END}")
            if not self.config.get("auto_confirm"):
                choice = input("Reinstall? (y/n): ").lower().strip()
                if choice not in ['y', 'yes']:
                    return False
        
        # backup system state
        backup_file = self.backup_system_state()
        
        # prepare install
        if self.supported_managers[manager]["needs_sudo"]:
            cmd = f"sudo {manager} -S {package}"
        else:
            cmd = f"{manager} -S {package}"
        
        if self.config.get("auto_confirm"):
            cmd += " --noconfirm"
        
        print(f"{Colors.BLUE}📦 Installing {package} with {manager}...{Colors.END}")
        
        success, output = self.run_command(cmd, capture_output=False)
        
        if success:
            print(f"{Colors.GREEN}✅ Package '{package}' installed successfully!{Colors.END}")
            self.logger.info(f"Successfully installed package: {package}")
            return True
        else:
            print(f"{Colors.RED}❌ Failed to install package '{package}'.{Colors.END}")
            self.logger.error(f"Failed to install package: {package}")
            if backup_file:
                print(f"{Colors.YELLOW}System backup available at: {backup_file}{Colors.END}")
            return False
    
    def remove_package(self, manager: str, package: str, mode: str = "simple") -> bool:
        """remove package"""
        if not self.validate_package_name(package):
            print(f"{Colors.RED}Invalid package name: {package}{Colors.END}")
            return False
        
        installed_packages = self.get_installed_packages()
        if package not in installed_packages:
            print(f"{Colors.YELLOW}Package '{package}' is not installed.{Colors.END}")
            return False
        
        backup_file = self.backup_system_state()
        
        mode_descriptions = {
            "simple": "Remove package only",
            "full": "Remove package and unused dependencies",
            "purge": "Remove package, dependencies, and clean cache"
        }
        
        print(f"{Colors.BLUE}🗑️  Removing {package} ({mode_descriptions.get(mode, mode)})...{Colors.END}")
        
        if mode in ["simple", "full", "purge"]:
            success, output = self.run_command(
                f"sudo pacman -Rns {package}" + (" --noconfirm" if self.config.get("auto_confirm") else ""),
                capture_output=False
            )
            
            if success:
                print(f"{Colors.GREEN}✅ Package '{package}' removed successfully!{Colors.END}")
                self.logger.info(f"Successfully removed package: {package}")
                
                if mode == "purge":
                    print(f"{Colors.BLUE}🧹 Cleaning package cache...{Colors.END}")
                    clean_success, _ = self.run_command(
                        "sudo pacman -Sc" + (" --noconfirm" if self.config.get("auto_confirm") else ""),
                        capture_output=False
                    )
                    if clean_success:
                        print(f"{Colors.GREEN}✅ Package cache cleaned successfully!{Colors.END}")
                    else:
                        print(f"{Colors.YELLOW}⚠️  Failed to clean package cache.{Colors.END}")
                
                return True
            else:
                print(f"{Colors.RED}❌ Failed to remove package '{package}'.{Colors.END}")
                self.logger.error(f"Failed to remove package: {package}")
                if backup_file:
                    print(f"{Colors.YELLOW}System backup available at: {backup_file}{Colors.END}")
                return False
        else:
            print(f"{Colors.RED}❌ Unknown removal mode '{mode}'.{Colors.END}")
            return False
    
    def update_system(self, manager: str, mode: str = "standard") -> bool:
        """update system packags"""
        backup_file = self.backup_system_state()
        
        mode_descriptions = {
            "standard": "Update official repository packages",
            "full": "Update all packages including AUR",
            "refresh": "Refresh package databases and update",
            "force": "Force refresh databases and update all packages"
        }
        
        print(f"{Colors.BLUE}🔄 Updating system ({mode_descriptions.get(mode, mode)})...{Colors.END}")
        
        commands = []
        
        if mode == "standard":
            if self.supported_managers[manager]["needs_sudo"]:
                commands.append(f"sudo {manager} -Syu")
            else:
                commands.append(f"{manager} -Syu")
        
        elif mode == "full":
            if manager in ["yay", "paru"]:
                commands.append(f"{manager} -Syu")
            else:
                if self.is_installed("yay"):
                    commands.append("yay -Syu")
                elif self.is_installed("paru"):
                    commands.append("paru -Syu")
                else:
                    commands.append("sudo pacman -Syu")
                    print(f"{Colors.YELLOW}Warning: No AUR helper available, updating official repos only{Colors.END}")
        
        elif mode == "refresh":
            if self.supported_managers[manager]["needs_sudo"]:
                commands.append(f"sudo {manager} -Syyu")
            else:
                commands.append(f"{manager} -Syyu")
        
        elif mode == "force":
            if manager in ["yay", "paru"]:
                commands.append(f"{manager} -Syyu")
            else:
                commands.append("sudo pacman -Syyu")
                if self.is_installed("yay"):
                    commands.append("yay -Syu")
                elif self.is_installed("paru"):
                    commands.append("paru -Syu")
        
        else:
            print(f"{Colors.RED}❌ Unknown update mode '{mode}'.{Colors.END}")
            return False
        
        if self.config.get("auto_confirm"):
            commands = [cmd + " --noconfirm" for cmd in commands]
        
        all_success = True
        for i, cmd in enumerate(commands):
            if len(commands) > 1:
                print(f"{Colors.CYAN}Step {i+1}/{len(commands)}: {cmd.split()[0]}{Colors.END}")
            
            success, output = self.run_command(cmd, capture_output=False)
            
            if not success:
                print(f"{Colors.RED}❌ Failed to execute: {cmd}{Colors.END}")
                self.logger.error(f"Update command failed: {cmd}")
                all_success = False
                break
        
        if all_success:
            print(f"{Colors.GREEN}✅ System update completed successfully!{Colors.END}")
            self.logger.info(f"System update completed successfully with mode: {mode}")
            
            orphaned_success, orphaned_output = self.run_command("pacman -Qtdq")
            if orphaned_success and orphaned_output.strip():
                print(f"{Colors.YELLOW}📦 Found orphaned packages: {len(orphaned_output.strip().split())} packages{Colors.END}")
                if not self.config.get("auto_confirm"):
                    choice = input(f"{Colors.YELLOW}Remove orphaned packages? (y/n): {Colors.END}").strip().lower()
                    if choice in ['y', 'yes']:
                        self.remove_orphaned_packages()
            
            return True
        else:
            print(f"{Colors.RED}❌ System update failed!{Colors.END}")
            if backup_file:
                print(f"{Colors.YELLOW}System backup available at: {backup_file}{Colors.END}")
            return False
    
    def remove_orphaned_packages(self) -> bool:
        """Remove orphaned packages from the system"""
        print(f"{Colors.BLUE}🧹 Checking for orphaned packages...{Colors.END}")
        
        success, output = self.run_command("pacman -Qtdq")
        if not success:
            print(f"{Colors.RED}❌ Failed to check for orphaned packages.{Colors.END}")
            return False
        
        if not output.strip():
            print(f"{Colors.GREEN}✅ No orphaned packages found.{Colors.END}")
            return True
        
        orphaned_packages = output.strip().split('\n')
        print(f"{Colors.YELLOW}Found {len(orphaned_packages)} orphaned packages:{Colors.END}")
        
        for pkg in orphaned_packages[:10]:
            print(f"  • {pkg}")
        
        if len(orphaned_packages) > 10:
            print(f"  ... and {len(orphaned_packages) - 10} more")
        
        if not self.config.get("auto_confirm"):
            choice = input(f"\n{Colors.YELLOW}Remove these orphaned packages? (y/n): {Colors.END}").strip().lower()
            if choice not in ['y', 'yes']:
                print(f"{Colors.BLUE}Orphaned package removal cancelled.{Colors.END}")
                return False
        
        backup_file = self.backup_system_state()
        
        remove_cmd = "sudo pacman -Rns $(pacman -Qtdq)"
        if self.config.get("auto_confirm"):
            remove_cmd += " --noconfirm"
        
        success, output = self.run_command(remove_cmd, capture_output=False)
        
        if success:
            print(f"{Colors.GREEN}✅ Orphaned packages removed successfully!{Colors.END}")
            self.logger.info(f"Removed {len(orphaned_packages)} orphaned packages")
            return True
        else:
            print(f"{Colors.RED}❌ Failed to remove orphaned packages.{Colors.END}")
            self.logger.error("Failed to remove orphaned packages")
            if backup_file:
                print(f"{Colors.YELLOW}System backup available at: {backup_file}{Colors.END}")
            return False
            print(f"{Colors.RED}❌ Unknown removal mode '{mode}'.{Colors.END}")
            return False
    
    def show_package_manager_menu(self) -> Optional[str]:
        print(f"\n{Colors.BOLD}{Colors.CYAN}🔧 Choose your package manager:{Colors.END}")
        
        available_managers = []
        for i, (key, info) in enumerate(self.supported_managers.items(), 1):
            status = "✅" if self.is_installed(key) else "❌"
            aur_support = "(AUR support)" if info["aur_support"] else "(Official repos only)"
            print(f"{i}. {status} {info['name']} {aur_support}")
            available_managers.append(key)
        
        print(f"{len(available_managers) + 1}. ⚙️  Configuration")
        print("0. Exit")
        
        try:
            choice = input(f"\n{Colors.YELLOW}Enter your choice: {Colors.END}").strip()
            
            if choice == "0":
                return None
            elif choice == str(len(available_managers) + 1):
                self.show_config_menu()
                return self.show_package_manager_menu()  # Return to manager selection
            else:
                choice_num = int(choice)
                if 1 <= choice_num <= len(available_managers):
                    selected = available_managers[choice_num - 1]
                    
                    if not self.is_installed(selected) and selected != "pacman":
                        if not self.install_helper(selected):
                            return self.show_package_manager_menu()  # Try again
                    
                    return selected
                else:
                    print(f"{Colors.RED}Invalid selection.{Colors.END}")
                    return self.show_package_manager_menu()
        
        except ValueError:
            print(f"{Colors.RED}Invalid input. Please enter a number.{Colors.END}")
            return self.show_package_manager_menu()
    
    def show_action_menu(self) -> Optional[str]:
        """Display action selection menu"""
        print(f"\n{Colors.BOLD}{Colors.GREEN}📋 Available Actions:{Colors.END}")
        print("1. 📦 Install package")
        print("2. 🗑️  Remove package (simple)")
        print("3. 🗑️  Remove package + unused dependencies")
        print("4. 🧹 PURGE package + clean cache")
        print("5. 🔄 Update system")
        print("6. 🔍 Search packages")
        print("7. 📊 Show system information")
        print("0. Back to manager selection")
        
        try:
            choice = input(f"\n{Colors.YELLOW}Choose an action: {Colors.END}").strip()
            return choice
        except KeyboardInterrupt:
            print(f"\n{Colors.BLUE}Operation cancelled.{Colors.END}")
            return None
    
    def show_config_menu(self):
        while True:
            print(f"\n{Colors.BOLD}{Colors.MAGENTA}⚙️  Configuration{Colors.END}")
            print(f"1. Default manager: {self.config.get('default_manager')}")
            print(f"2. Auto-confirm operations: {self.config.get('auto_confirm')}")
            print(f"3. Show progress indicators: {self.config.get('show_progress')}")
            print(f"4. Backup before operations: {self.config.get('backup_before_operations')}")
            print(f"5. Max search results: {self.config.get('max_search_results')}")
            print(f"6. Colors enabled: {self.config.get('colors_enabled')}")
            print("0. Back")
            
            try:
                choice = input(f"\n{Colors.YELLOW}Select option to modify: {Colors.END}").strip()
                
                if choice == "0":
                    break
                elif choice == "1":
                    print("Available managers: pacman, yay, paru")
                    new_manager = input("Enter default manager: ").strip().lower()
                    if new_manager in self.supported_managers:
                        self.config.set('default_manager', new_manager)
                        print(f"{Colors.GREEN}Default manager set to {new_manager}{Colors.END}")
                elif choice == "2":
                    self.config.set('auto_confirm', not self.config.get('auto_confirm'))
                    print(f"{Colors.GREEN}Auto-confirm toggled{Colors.END}")
                elif choice == "3":
                    self.config.set('show_progress', not self.config.get('show_progress'))
                    print(f"{Colors.GREEN}Progress indicators toggled{Colors.END}")
                elif choice == "4":
                    self.config.set('backup_before_operations', not self.config.get('backup_before_operations'))
                    print(f"{Colors.GREEN}Backup setting toggled{Colors.END}")
                elif choice == "5":
                    try:
                        max_results = int(input("Enter max search results (1-50): "))
                        if 1 <= max_results <= 50:
                            self.config.set('max_search_results', max_results)
                            print(f"{Colors.GREEN}Max search results set to {max_results}{Colors.END}")
                    except ValueError:
                        print(f"{Colors.RED}Invalid number{Colors.END}")
                elif choice == "6":
                    self.config.set('colors_enabled', not self.config.get('colors_enabled'))
                    print(f"{Colors.GREEN}Colors toggled{Colors.END}")
                
            except KeyboardInterrupt:
                break
    
    def show_system_info(self):
        print(f"\n{Colors.BOLD}{Colors.CYAN}📊 System Information{Colors.END}")
        
        installed_packages = self.get_installed_packages()
        print(f"📦 Installed packages: {len(installed_packages)}")
        
        print(f"\n{Colors.BOLD}Available Package Managers:{Colors.END}")
        for manager, info in self.supported_managers.items():
            status = "✅ Installed" if self.is_installed(manager) else "❌ Not installed"
            print(f"  {info['name']}: {status}")
        
        try:
            if os.path.exists(self.logger.log_file):
                print(f"\n{Colors.BOLD}Recent Operations:{Colors.END}")
                with open(self.logger.log_file, 'r') as f:
                    lines = f.readlines()[-5:]  # Last 5 operations
                    for line in lines:
                        print(f"  {line.strip()}")
        except Exception:
            pass
        
        input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.END}")
    
    def run(self):
        print(f"{Colors.BOLD}{Colors.BLUE}")
        print("╔════════════════════════════════════════════════════════════╗")
        print("║                    AUR Helper Enhanced                     ║")
        print("║            Advanced Package Manager Interface              ║")
        print("╚════════════════════════════════════════════════════════════╝")
        print(f"{Colors.END}")
        
        try:
            while True:
                manager = self.show_package_manager_menu()
                if not manager:
                    print(f"{Colors.BLUE}Goodbye! 👋{Colors.END}")
                    break
                
                self.current_manager = manager
                print(f"\n{Colors.GREEN}Using {self.supported_managers[manager]['name']}{Colors.END}")
                
                while True:
                    action = self.show_action_menu()
                    if not action or action == "0":
                        break
                    
                    if action == "1":
                        package = input(f"\n{Colors.YELLOW}Enter package name to install: {Colors.END}").strip()
                        if package:
                            if not self.check_package_exists(manager, package):
                                package = self.search_similar_interactive(manager, package)
                                if not package:
                                    continue
                            self.install_package(manager, package)
                    
                    elif action == "2":
                        package = input(f"\n{Colors.YELLOW}Enter package name to remove: {Colors.END}").strip()
                        if package:
                            self.remove_package(manager, package, "simple")
                    
                    elif action == "3":
                        package = input(f"\n{Colors.YELLOW}Enter package name to remove: {Colors.END}").strip()
                        if package:
                            self.remove_package(manager, package, "full")
                    
                    elif action == "4":
                        package = input(f"\n{Colors.YELLOW}Enter package name to purge: {Colors.END}").strip()
                        if package:
                            print(f"{Colors.RED}Warning: This will remove the package, dependencies, and clean cache!{Colors.END}")
                            if self.config.get("auto_confirm") or input("Continue? (y/n): ").lower().strip() in ['y', 'yes']:
                                self.remove_package(manager, package, "purge")
                    
                    elif action == "5":
                        print(f"\n{Colors.BOLD}{Colors.CYAN}🔄 System Update Options:{Colors.END}")
                        print("1. Standard update (official repos)")
                        print("2. Full update (including AUR)")
                        print("3. Refresh databases and update")
                        print("4. Force refresh and full update")
                        print("0. Cancel")
                        
                        update_choice = input(f"\n{Colors.YELLOW}Choose update mode: {Colors.END}").strip()
                        
                        update_modes = {
                            "1": "standard",
                            "2": "full", 
                            "3": "refresh",
                            "4": "force"
                        }
                        
                        if update_choice in update_modes:
                            self.update_system(manager, update_modes[update_choice])
                        elif update_choice != "0":
                            print(f"{Colors.RED}Invalid update option.{Colors.END}")
                    
                    elif action == "6":
                        query = input(f"\n{Colors.YELLOW}Enter search query: {Colors.END}").strip()
                        if query:
                            self.search_similar_interactive(manager, query)
                    
                    elif action == "7":
                        self.show_system_info()
                    
                    else:
                        print(f"{Colors.RED}Invalid action.{Colors.END}")
        
        except KeyboardInterrupt:
            print(f"\n{Colors.BLUE}Interrupted by user. Goodbye! 👋{Colors.END}")
        except Exception as e:
            print(f"{Colors.RED}An unexpected error occurred: {e}{Colors.END}")
            self.logger.error(f"Unexpected error: {e}")


def main():
    try:
        helper = AURHelper()
        helper.run()
    except Exception as e:
        print(f"Failed to start AUR Helper: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

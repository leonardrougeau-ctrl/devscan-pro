#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import subprocess
import threading
import datetime
import os
import sys
import platform
import json
import shutil
import hashlib
import requests
import uuid
from pathlib import Path

class LicenseValidator:
    def __init__(self):
        # CHANGE TO YOUR SERVER
        self.validation_url = "https://clearwatercodes.com/license_manager/api/validate"
        self.activation_url = "https://clearwatercodes.com/license_manager/api/validate"  # Same endpoint
        self.app_name = "DevScan_Pro"
        self.license_file = Path.home() / ".devscan_pro_license.json"
                           
    def validate_license(self, license_key):
        """Validate license against your server"""
        try:
            # Add system fingerprint to prevent key sharing
            system_fingerprint = self.get_system_fingerprint()
            
            response = requests.post(
                self.validation_url,
                json={
                    "key": license_key,
                    "app_name": self.app_name,
                    "system_id": system_fingerprint  # Add fingerprint
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result['valid']:
                    # Save successful validation
                    self._save_license_info(license_key, result)
                    return True, "✅ License activated! Premium features unlocked.", result.get('customer', '')
                else:
                    return False, f"❌ {result.get('message', 'Invalid license')}", None
            else:
                return False, "❌ Server error. Please try again later.", None
                
        except Exception as e:
            # Fallback to offline validation
            offline_valid, offline_msg = self._check_offline_validation(license_key)
            if offline_valid:
                return True, offline_msg, "Offline User"
            return False, f"❌ Connection failed: {str(e)}", None
    
    def _save_license_info(self, license_key, validation_result):
        """Save license info for offline validation"""
        license_data = {
            'license_key': license_key,
            'last_validation': datetime.datetime.now().isoformat(),
            'customer': validation_result.get('customer', ''),
            'expires': validation_result.get('expires', ''),
            'app_name': self.app_name
        }
        
        with open(self.license_file, 'w') as f:
            json.dump(license_data, f, indent=2)
    
    def _check_offline_validation(self, license_key, grace_hours=24):
        """Check if license was recently validated offline"""
        try:
            if not self.license_file.exists():
                return False, "No offline license found"
            
            with open(self.license_file, 'r') as f:
                license_data = json.load(f)
            
            # Check if it's the same license key
            if license_data.get('license_key') != license_key:
                return False, "License key mismatch"
            
            # Check if within grace period
            last_valid = datetime.datetime.fromisoformat(license_data['last_validation'])
            grace_period = datetime.timedelta(hours=grace_hours)
            
            if datetime.datetime.now() - last_valid < grace_period:
                return True, "✅ License valid (offline mode)"
            else:
                return False, "❌ Offline period expired. Internet required."
                
        except Exception as e:
            return False, f"Offline check failed: {str(e)}"
    
    def get_license_info(self):
        """Get stored license information"""
        try:
            if self.license_file.exists():
                with open(self.license_file, 'r') as f:
                    return json.load(f)
        except:
            return None
    
    def clear_license(self):
        """Remove license file (for testing)"""
        try:
            if self.license_file.exists():
                self.license_file.unlink()
                return True
        except:
            return False

    def get_system_fingerprint(self):
        """Generate unique system fingerprint to prevent key sharing"""
        try:
            # Method 1: Use machine-id (Linux systems)
            if os.path.exists('/etc/machine-id'):
                with open('/etc/machine-id', 'r') as f:
                    machine_id = f.read().strip()
                return hashlib.md5(machine_id.encode()).hexdigest()
            
            # Method 2: Use hostname and MAC address as fallback
            hostname = platform.node()
            mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                                   for elements in range(0,8*6,8)][::-1])
            system_info = f"{hostname}-{mac_address}"
            return hashlib.md5(system_info.encode()).hexdigest()
            
        except Exception as e:
            # Final fallback - less secure but better than nothing
            return hashlib.md5(str(uuid.getnode()).encode()).hexdigest()

class DevScanPro:
    def __init__(self, root):
        self.root = root
        self.root.title("DevScan Pro - Professional Development Tools Scanner")
        self.root.geometry("1000x750")
        self.root.configure(bg='#2b2b2b')
        
        # Application info
        self.app_name = "DevScan Pro"
        self.version = "1.0.0"
        self.vendor = "DevScan Pro"
        
        # License management
        self.license_file = "licenses/trial_data.json"
        self.activation_file = "licenses/activation.json"
        self.licenses_dir = "licenses"
        self.license_validator = LicenseValidator()
        
        # Create licenses directory if it doesn't exist
        os.makedirs(self.licenses_dir, exist_ok=True)
        
        # Initialize license system
        self.trial_days = 30
        self.max_exports = 5
        self.initialize_license_system()
        
        # Detect Ubuntu version
        self.ubuntu_version = self.get_ubuntu_version()
        
        # Package manager mappings
        self.package_manager_commands = {
            'apt': 'sudo apt install',
            'snap': 'sudo snap install',
            'pip': 'pip install',
            'pip3': 'pip3 install',
            'npm': 'npm install -g',
            'cargo': 'cargo install'
        }
        
        # Tool to package mappings
        self.tool_packages = {
            # Programming Languages
            "Python 3": {"package": "python3", "manager": "apt"},
            "Python": {"package": "python", "manager": "apt"},
            "Node.js": {"package": "nodejs", "manager": "apt"},
            "npm": {"package": "npm", "manager": "apt"},
            "npx": {"package": "npm", "manager": "apt"},  # Comes with npm
            "Java": {"package": "default-jdk", "manager": "apt"},
            "PHP": {"package": "php", "manager": "apt"},
            "Go": {"package": "golang", "manager": "apt"},
            "Ruby": {"package": "ruby", "manager": "apt"},
            "Perl": {"package": "perl", "manager": "apt"},
            "Rust": {"package": "rustc", "manager": "apt"},
            
            # Build Tools
            "Git": {"package": "git", "manager": "apt"},
            "GNU Make": {"package": "make", "manager": "apt"},
            "GCC": {"package": "gcc", "manager": "apt"},
            "G++": {"package": "g++", "manager": "apt"},
            "CMake": {"package": "cmake", "manager": "apt"},
            "pip": {"package": "python3-pip", "manager": "apt"},
            "pip3": {"package": "python3-pip", "manager": "apt"},
           
            # Containers & Virtualization
            "Docker": {"package": "docker.io", "manager": "apt"},
            "Docker Compose": {"package": "docker-compose", "manager": "apt"},
            "Podman": {"package": "podman", "manager": "apt"},
            "Kubernetes CLI": {"package": "kubectl", "manager": "snap"},
            "Vagrant": {"package": "vagrant", "manager": "apt"},
            
            # Editors & IDEs
            "VS Code": {"package": "code", "manager": "snap"},
            "Vim": {"package": "vim", "manager": "apt"},
            "Nano": {"package": "nano", "manager": "apt"},
            "Emacs": {"package": "emacs", "manager": "apt"},
            
            # Databases
            "PostgreSQL": {"package": "postgresql", "manager": "apt"},
            "MySQL": {"package": "mysql-server", "manager": "apt"},
            "SQLite": {"package": "sqlite3", "manager": "apt"},
            "MongoDB": {"package": "mongodb", "manager": "apt"},
            
            # System Tools
            "cURL": {"package": "curl", "manager": "apt"},
            "Wget": {"package": "wget", "manager": "apt"},
            "rsync": {"package": "rsync", "manager": "apt"},
            "tar": {"package": "tar", "manager": "apt"},
            
            # Package Managers
            "APT": {"package": "apt", "manager": "apt"},
            "Snap": {"package": "snapd", "manager": "apt"},
            "Flatpak": {"package": "flatpak", "manager": "apt"},
            
            # Networking
            "netstat": {"package": "net-tools", "manager": "apt"},
            "iproute2": {"package": "iproute2", "manager": "apt"},
            "Nmap": {"package": "nmap", "manager": "apt"},
            
            # Development Tools
            "Gitk": {"package": "git", "manager": "apt"},  # Comes with git
            "Git GUI": {"package": "git", "manager": "apt"},  # Comes with git
            "Meld": {"package": "meld", "manager": "apt"},
        }
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header with trial info
        header_frame = tk.Frame(main_frame, bg='#2b2b2b')
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Title with trial status
        trial_status = self.get_trial_status()
        title_text = f"🔧 {self.app_name} - {trial_status}"
        title_label = tk.Label(header_frame, text=title_text, 
                              font=("Ubuntu", 18, "bold"), 
                              bg='#2b2b2b', fg='#ffffff')
        title_label.pack(side=tk.LEFT)
        
        # Version and license info
        info_text = f"v{self.version} | Exports: {self.export_count}/{self.max_exports}"
        info_label = tk.Label(header_frame, text=info_text, 
                             font=("Ubuntu", 10), 
                             bg='#2b2b2b', fg='#888888')
        info_label.pack(side=tk.RIGHT)

        # Button frame
        button_frame = tk.Frame(main_frame, bg='#2b2b2b')
        button_frame.pack(pady=(0, 15))

        # Refresh button
        self.check_btn = tk.Button(button_frame, text="🔄 Refresh Tools", 
                                  command=self.check_tools,
                                  bg='#28a745', fg='white',
                                  font=("Ubuntu", 12, "bold"),
                                  padx=15, pady=8)
        self.check_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Export button
        self.export_btn = tk.Button(button_frame, text="💾 Export Report", 
                                   command=self.export_to_file,
                                   bg='#007acc', fg='white',
                                   font=("Ubuntu", 12, "bold"),
                                   padx=15, pady=8)
        self.export_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Copy button
        self.copy_btn = tk.Button(button_frame, text="📋 Copy Results", 
                                 command=self.copy_to_clipboard,
                                 bg='#6c757d', fg='white',
                                 font=("Ubuntu", 12, "bold"),
                                 padx=15, pady=8)
        self.copy_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # System Info button
        self.info_btn = tk.Button(button_frame, text="ℹ️ System Info", 
                                 command=self.show_system_info,
                                 bg='#17a2b8', fg='white',
                                 font=("Ubuntu", 12, "bold"),
                                 padx=15, pady=8)
        self.info_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Export Installation Script button
        self.export_script_btn = tk.Button(button_frame, text="📦 Export Install Script", 
                                         command=self.export_installation_script,
                                         bg='#9c27b0', fg='white',
                                         font=("Ubuntu", 12, "bold"),
                                         padx=15, pady=8)
        self.export_script_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # NEW: Selective Export button
        self.selective_export_btn = tk.Button(button_frame, text="🎯 Selective Export", 
                                            command=self.show_selective_export_dialog,
                                            bg='#ff5722', fg='white',
                                            font=("Ubuntu", 12, "bold"),
                                            padx=15, pady=8)
        self.selective_export_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # License activation text box (replaces the license button)
        license_activation_frame = tk.Frame(button_frame, bg='#2d2d2d')
        license_activation_frame.pack(side=tk.LEFT, padx=5)

        self.license_var = tk.StringVar()
        self.license_entry = tk.Entry(
            license_activation_frame,
            textvariable=self.license_var,
            width=25,
            font=('Arial', 10),
            bg='#1e1e1e',
            fg='#888888',
            relief='flat',
            insertbackground='white'
        )
        self.license_entry.insert(0, "Enter license code here...")
        self.license_entry.pack(pady=5, padx=10)

        # Bind events for placeholder text and real-time validation
        self.license_entry.bind('<FocusIn>', self.clear_license_placeholder)
        self.license_entry.bind('<FocusOut>', self.restore_license_placeholder)
        self.license_var.trace('w', self.validate_license_real_time)

        # Category filter
        filter_frame = tk.Frame(main_frame, bg='#2b2b2b')
        filter_frame.pack(pady=(0, 10), fill=tk.X)

        tk.Label(filter_frame, text="Filter Category:", 
                bg='#2b2b2b', fg='#ffffff', font=("Ubuntu", 10)).pack(side=tk.LEFT, padx=(0, 10))

        self.filter_var = tk.StringVar(value="All")
        categories = ["All", "Programming", "Build Tools", "Containers", "System", "Editors", "Databases", "Networking"]
        for category in categories:
            tk.Radiobutton(filter_frame, text=category, variable=self.filter_var, 
                          value=category, bg='#2b2b2b', fg='#ffffff',
                          selectcolor='#2b2b2b', font=("Ubuntu", 9),
                          command=self.apply_filter).pack(side=tk.LEFT, padx=5)
            
            # Results frame with scrollbar
        results_container = ttk.Frame(main_frame)
        results_container.pack(fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(results_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Canvas for scrolling
        self.canvas = tk.Canvas(results_container, yscrollcommand=scrollbar.set, 
                               bg='#1e1e1e', highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.canvas.yview)

        # Results frame inside canvas
        self.results_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.results_frame, anchor="nw")

        # Configure canvas scrolling
        self.results_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Add mouse wheel scrolling
        self._bind_mouse_wheel()

        # Status label
        self.status_label = tk.Label(main_frame, text="Ready to check development tools", 
                                    bg='#2b2b2b', fg='#00ff00', font=("Ubuntu", 10))
        self.status_label.pack(pady=(15, 0), anchor='w')

        # Store results for export/copy
        self.current_results = []
        self.all_results = []
        self.tool_checkboxes = {}  # NEW: Store checkboxes for selective export
        
        # Auto-check on startup
        self.root.after(1000, self.check_tools)

    # LICENSE TEXT BOX METHODS
    def clear_license_placeholder(self, event):
        if self.license_entry.get() == "Enter license code here...":
            self.license_entry.delete(0, tk.END)
            self.license_entry.configure(fg='#ffffff')

    def restore_license_placeholder(self, event):
        if not self.license_entry.get():
            self.license_entry.insert(0, "Enter license code here...")
            self.license_entry.configure(fg='#888888')

    def validate_license_real_time(self, *args):
        license_key = self.license_var.get().strip()
        
        # Skip validation if it's placeholder text or too short
        if (license_key == "Enter license code here..." or 
            len(license_key) < 10 or 
            not license_key):
            return
            
        # Validate license when user stops typing (debounce)
        if hasattr(self, '_license_validation_job'):
            self.root.after_cancel(self._license_validation_job)
        
        self._license_validation_job = self.root.after(1000, lambda: self.do_license_validation(license_key))

    def do_license_validation(self, license_key):
        is_valid, message, customer = self.validate_license_server(license_key)
        if is_valid:
            self.activated = True
            self.license_key = license_key.upper()
            self.save_license_data()
            self.license_entry.configure(fg='#00ff00')  # Green for success
            # Show success message
            self.status_label.config(text="✅ License activated! All features unlocked.", fg='#00ff00')
            
            self.refresh_ui_after_activation()
        
            # Optionally hide the entry after successful activation
            self.root.after(3000, self.hide_license_entry)
        else:
            self.license_entry.configure(fg='#ff4444')  # Red for error
            self.status_label.config(text="❌ Invalid license key", fg='#ff4444')
            self.root.after(3000, self.clear_license_entry)

    def refresh_ui_after_activation(self):
        """Refresh UI elements to show licensed status"""
        # Update the header title
        trial_status = self.get_trial_status()
        title_text = f"🔧 {self.app_name} - {trial_status}"
        
        # You might need to update the title label directly
        # This depends on how your header is structured
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label) and "🔧" in child.cget("text"):
                        child.config(text=title_text)
                        break  
        else:
            self.license_entry.configure(fg='#ff4444')  # Red for error
            self.status_label.config(text="❌ Invalid license key", fg='#ff4444')
            self.root.after(3000, self.clear_license_entry)

    def hide_license_entry(self):
        # Hide the license entry after successful activation
        self.license_entry.pack_forget()

    def clear_license_entry(self):
        # CORRECTED: Only 3 lines - no corrupted code!
        self.license_var.set("")
        self.restore_license_placeholder(None)
        self.status_label.config(text="Ready to check development tools", fg='#00ff00')

    # LICENSE SYSTEM METHODS
    def initialize_license_system(self):
        """Initialize or load trial data"""
        print("DEBUG: Initializing license system...")
        
        # Create licenses directory if it doesn't exist
        os.makedirs(self.licenses_dir, exist_ok=True)
        
        if os.path.exists(self.license_file):
            try:
                with open(self.license_file, 'r') as f:
                    data = json.load(f)
                    self.first_run = data.get('first_run', datetime.datetime.now().isoformat())
                    self.export_count = data.get('export_count', 0)
                    self.activated = data.get('activated', False)
                    self.license_key = data.get('license_key', '')
                print(f"DEBUG: Loaded license data - activated: {self.activated}")
            except Exception as e:
                print(f"DEBUG: Error loading license file: {e}")
                self.reset_trial_data()
        else:
            print("DEBUG: No license file found, creating new trial data")
            self.reset_trial_data()
        
        # Check if activated via license server
        try:
            server_license_info = self.license_validator.get_license_info()
            print(f"DEBUG: Server license info: {server_license_info}")
            
            if server_license_info and server_license_info.get('license_key'):
                print("DEBUG: Found server license, activating...")
                self.activated = True
                self.license_key = server_license_info['license_key']
                self.save_license_data()
        except Exception as e:
            print(f"DEBUG: Server license check failed: {e}")
        
        print(f"DEBUG: License initialization complete - activated: {self.activated}")

    def reset_trial_data(self):
        """Reset trial data for new installation"""
        self.first_run = datetime.datetime.now().isoformat()
        self.export_count = 0
        self.activated = False
        self.license_key = ""
        self.save_license_data()

    def save_license_data(self):
        """Save license data to file"""
        data = {
            'first_run': self.first_run,
            'export_count': self.export_count,
            'activated': self.activated,
            'license_key': self.license_key
        }
        with open(self.license_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get_trial_status(self):
        """Get trial status message"""
        if self.activated:
            return "✅ Licensed Version"
        
        days_remaining = self.get_trial_days_remaining()
        if days_remaining <= 0:
            return "❌ Trial Expired"
        else:
            return f"⏰ Trial: {days_remaining} days remaining"

    def get_trial_days_remaining(self):
        """Calculate days remaining in trial"""
        if self.activated:
            return 999  # Unlimited for activated licenses
        
        first_run_date = datetime.datetime.fromisoformat(self.first_run)
        current_date = datetime.datetime.now()
        days_passed = (current_date - first_run_date).days
        days_remaining = self.trial_days - days_passed
        
        return max(0, days_remaining)

    def validate_license_server(self, license_key):
        """Validate license key against license server"""
        return self.license_validator.validate_license(license_key)

    def check_trial_limits(self):
        """Check if trial limits are exceeded"""
        if self.activated:
            return True  # No limits for activated licenses
        
        # Check trial period
        if self.get_trial_days_remaining() <= 0:
            messagebox.showerror(
                "Trial Expired", 
                "Your 30-day trial has expired.\n\n"
                "Please purchase a license to continue using DevScan Pro.\n\n"
                "Visit: https://clearwatercodes.com/purchase"
            )
            return False
        
        # Check export limit
        if self.export_count >= self.max_exports:
            messagebox.showerror(
                "Export Limit Reached", 
                f"You have reached the maximum of {self.max_exports} exports in the trial version.\n\n"
                "Please purchase a license for unlimited exports.\n\n"
                "Visit: https://clearwatercodes.com/purchase"
            )
            return False
        
        return True

    def show_license_info(self):
        """Show license information dialog"""
        days_remaining = self.get_trial_days_remaining()
        
        if self.activated:
            server_info = self.license_validator.get_license_info()
            customer_name = server_info.get('customer', 'Unknown') if server_info else 'Unknown'
            
            message = f"""✅ Licensed Version

Your DevScan Pro license is activated and valid.

Customer: {customer_name}
License Key: {self.license_key}
Features: Unlimited usage, all features enabled

Thank you for your purchase!"""
        else:
            message = f"""🔍 DevScan Pro Trial Version

Trial Status: {days_remaining} days remaining
Exports Used: {self.export_count}/{self.max_exports}

Trial Features:
• Full tool detection (50+ tools)
• System information
• {self.max_exports} exports (TXT/JSON)
• All scanning capabilities
• Installation script export
• Selective export

After trial:
• Purchase for unlimited exports
• Lifetime updates
• Priority support

Activate License:
Enter your license key in the text box above."""

        # Create license dialog
        license_window = tk.Toplevel(self.root)
        license_window.title("DevScan Pro License Information")
        license_window.geometry("500x400")
        license_window.configure(bg='#2b2b2b')
        
        # License text
        text_frame = tk.Frame(license_window, bg='#2b2b2b')
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        license_text = tk.Text(text_frame, wrap=tk.WORD, bg='#1e1e1e', fg='#ffffff', 
                              font=("Ubuntu", 10), relief='flat')
        license_text.pack(fill=tk.BOTH, expand=True)
        license_text.insert(tk.END, message)
        license_text.config(state=tk.DISABLED)
        
        # Buttons
        button_frame = tk.Frame(license_window, bg='#2b2b2b')
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # REMOVED: The activate button since we now have the text box
        
        purchase_btn = tk.Button(button_frame, text="Purchase License", 
                               command=self.open_purchase_page,
                               bg='#2196F3', fg='white',
                               font=("Ubuntu", 10, "bold"))
        purchase_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        close_btn = tk.Button(button_frame, text="Close", 
                            command=license_window.destroy,
                            bg='#666', fg='white',
                            font=("Ubuntu", 10))
        close_btn.pack(side=tk.RIGHT)

    def activate_license(self):
        """Activate license with key via license server"""
        license_key = simpledialog.askstring(
            "Activate License", 
            "Enter your DevScan Pro license key:",
            parent=self.root
        )
        
        if license_key:
            # Validate against license server
            is_valid, message, customer = self.validate_license_server(license_key)
            
            if is_valid:
                self.activated = True
                self.license_key = license_key.upper()
                self.save_license_data()
                
                messagebox.showinfo("Activation Successful", 
                                  f"Your DevScan Pro license has been activated!\n\n"
                                  f"Licensed to: {customer}\n"
                                  f"Thank you for your purchase. All features are now unlocked.")
                
                # Refresh UI to show licensed status
                self.root.after(100, self.check_tools)
            else:
                messagebox.showerror("Invalid License", 
                                   f"The license key you entered is invalid.\n\n"
                                   f"{message}\n\n"
                                   "Please check your key and try again, or contact support@devscan.pro")

    def open_purchase_page(self):
        """Open purchase page in browser"""
        import webbrowser
        webbrowser.open("https://clearwatercodes.com/purchase")
        messagebox.showinfo("Purchase DevScan Pro", 
                          "Opening purchase page in your browser...\n\n"
                          "After purchase, you will receive your license key via email.")

    def get_ubuntu_version(self):
        """Get Ubuntu version information"""
        try:
            result = subprocess.run(['lsb_release', '-d'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.split(':')[1].strip()
        except:
            pass
        return platform.version()
    
        # UI SCROLLING METHODS
    def _bind_mouse_wheel(self):
        """Bind mouse wheel events for scrolling"""
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Button-4>", self._on_mouse_wheel)
        self.canvas.bind("<Button-5>", self._on_mouse_wheel)
        self.results_frame.bind("<MouseWheel>", self._on_mouse_wheel)
        self.results_frame.bind("<Button-4>", self._on_mouse_wheel)
        self.results_frame.bind("<Button-5>", self._on_mouse_wheel)

    def _on_mouse_wheel(self, event):
        """Handle mouse wheel scrolling"""
        if event.delta:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    # TOOL CHECKING METHODS
    def check_tool(self, command, name, category="System", check_type="version"):
        try:
            if check_type == "version":
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    output = result.stdout.strip().split('\n')[0]
                    return output, "installed", category
                else:
                    return "Not installed", "not_installed", category
                    
            elif check_type == "package":
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return "Installed", "installed", category
                else:
                    return "Not installed", "not_installed", category
                    
            elif check_type == "which":
                result = subprocess.run(f"which {command}", shell=True, capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return f"Found: {result.stdout.strip()}", "installed", category
                else:
                    return "Not in PATH", "not_installed", category
                    
            elif check_type == "service":
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return "Available", "installed", category
                else:
                    return "Not available", "not_installed", category
                    
            elif check_type == "snap":
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return "Snap installed", "installed", category
                else:
                    return "Snap not installed", "not_installed", category
                    
        except subprocess.TimeoutExpired:
            return "Timeout", "not_installed", category
        except Exception as e:
            return f"Error: {str(e)}", "not_installed", category
        
    def check_tools(self):
        self.check_btn.config(state='disabled', text="🔄 Checking...")
        self.export_btn.config(state='disabled')
        self.copy_btn.config(state='disabled')
        self.info_btn.config(state='disabled')
        self.export_script_btn.config(state='disabled')
        self.selective_export_btn.config(state='disabled')
        self.status_label.config(text="Scanning system for development tools...", fg='#ffff00')
        
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        # Ubuntu-specific tools list
        tools = [
            # System Information
            ("lsb_release -a", "Ubuntu Version", "System", "version"),
            ("uname -r", "Kernel Version", "System", "version"),
            
            # Programming Languages
            ("python3 --version", "Python 3", "Programming", "version"),
            ("python --version", "Python", "Programming", "version"),
            ("node --version", "Node.js", "Programming", "version"),
            ("npm --version", "npm", "Programming", "version"),
            ("npx --version", "npx", "Programming", "version"),
            ("java -version", "Java", "Programming", "version"),
            ("php --version", "PHP", "Programming", "version"),
            ("go version", "Go", "Programming", "version"),
            ("ruby --version", "Ruby", "Programming", "version"),
            ("perl --version", "Perl", "Programming", "version"),
            ("rustc --version", "Rust", "Programming", "version"),
            
            # Build Tools
            ("git --version", "Git", "Build Tools", "version"),
            ("make --version", "GNU Make", "Build Tools", "version"),
            ("gcc --version", "GCC", "Build Tools", "version"),
            ("g++ --version", "G++", "Build Tools", "version"),
            ("cmake --version", "CMake", "Build Tools", "version"),
            ("pip --version", "pip", "Build Tools", "version"),
            ("pip3 --version", "pip3", "Build Tools", "version"),
            
            # Containers & Virtualization
            ("docker --version", "Docker", "Containers", "version"),
            ("docker-compose --version", "Docker Compose", "Containers", "version"),
            ("podman --version", "Podman", "Containers", "version"),
            ("kubectl version --client", "Kubernetes CLI", "Containers", "version"),
            ("vagrant --version", "Vagrant", "Containers", "version"),
            
            # Editors & IDEs
            ("code --version", "VS Code", "Editors", "version"),
            ("vim --version", "Vim", "Editors", "version"),
            ("nano --version", "Nano", "Editors", "version"),
            ("emacs --version", "Emacs", "Editors", "version"),
            
            # Databases
            ("psql --version", "PostgreSQL", "Databases", "version"),
            ("mysql --version", "MySQL", "Databases", "version"),
            ("sqlite3 --version", "SQLite", "Databases", "version"),
            ("mongod --version", "MongoDB", "Databases", "version"),
            
            # System Tools
            ("curl --version", "cURL", "System", "version"),
            ("wget --version", "Wget", "System", "version"),
            ("ssh -V", "SSH", "System", "version"),
            ("rsync --version", "rsync", "System", "version"),
            ("tar --version", "tar", "System", "version"),
            
            # Package Managers
            ("apt --version", "APT", "System", "version"),
            ("snap --version", "Snap", "System", "version"),
            ("flatpak --version", "Flatpak", "System", "version"),
            
            # Networking
            ("netstat --version", "netstat", "Networking", "version"),
            ("ip --version", "iproute2", "Networking", "version"),
            ("nmap --version", "Nmap", "Networking", "version"),
            
            # Development Tools
            ("gitk --version", "Gitk", "Build Tools", "version"),
            ("git-gui --version", "Git GUI", "Build Tools", "version"),
            ("meld --version", "Meld", "Editors", "version"),
        ]
        
        # Run in thread to avoid freezing GUI
        thread = threading.Thread(target=self._check_tools_thread, args=(tools,))
        thread.daemon = True
        thread.start()

    def _check_tools_thread(self, tools):
        try:
            results = []
            
            for command, name, category, check_type in tools:
                version, status, cat = self.check_tool(command, name, category, check_type)
                results.append((name, version, status, cat))
            
            self.root.after(0, self._display_results, results)
            
        except Exception as e:
            error_result = [("Error", f"Scan failed: {str(e)}", "not_installed", "System")]
            self.root.after(0, self._display_results, error_result)
    
    def _display_results(self, results):
        self.all_results = results
        self.apply_filter()
        
        self.check_btn.config(state='normal', text="🔄 Refresh Tools")
        self.export_btn.config(state='normal')
        self.copy_btn.config(state='normal')
        self.info_btn.config(state='normal')
        self.export_script_btn.config(state='normal')
        self.selective_export_btn.config(state='normal')
        
        installed_count = sum(1 for _, _, status, _ in self.all_results if status == "installed")
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if installed_count > 0:
            self.status_label.config(text=f"✅ Found {installed_count}/{len(self.all_results)} tools installed • {current_time}", fg='#00ff00')
        else:
            self.status_label.config(text=f"❌ No development tools found • {current_time}", fg='#ff4444')
    
    def apply_filter(self):
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        filter_category = self.filter_var.get()
        
        if filter_category == "All":
            filtered_results = self.all_results
        else:
            filtered_results = [r for r in self.all_results if r[3] == filter_category]
        
        self.current_results = filtered_results
        
        if not filtered_results:
            empty_frame = tk.Frame(self.results_frame, bg='#1e1e1e')
            empty_frame.pack(fill=tk.X, pady=20)
            empty_label = tk.Label(empty_frame, text="No tools found in this category", 
                                 bg='#1e1e1e', fg='#666', font=("Ubuntu", 10))
            empty_label.pack()
            return
        
        categories = {}
        for name, version, status, category in filtered_results:
            if category not in categories:
                categories[category] = []
            categories[category].append((name, version, status))
        
        # Clear checkboxes dictionary
        self.tool_checkboxes = {}
        
        for category, tools in categories.items():
            if len(categories) > 1:
                cat_frame = tk.Frame(self.results_frame, bg='#3a3a3a', relief='raised', bd=1)
                cat_frame.pack(fill=tk.X, pady=(10, 5), padx=5)
                cat_label = tk.Label(cat_frame, text=category, bg='#3a3a3a', 
                                   font=("Ubuntu", 11, "bold"), fg='#ffffff', anchor='w')
                cat_label.pack(fill=tk.X, padx=10, pady=5)
            
            for name, version, status in tools:
                frame = tk.Frame(self.results_frame, bg='#2d2d2d', relief='flat', bd=1)
                frame.pack(fill=tk.X, pady=1, padx=5, anchor='w')
                
                checkbox_color = '#4CAF50' if status == "installed" else '#f44336'
                checkbox_canvas = tk.Canvas(frame, width=20, height=20, bg='#2d2d2d', highlightthickness=0)
                checkbox_canvas.pack(side=tk.LEFT, padx=(10, 15))
                checkbox_canvas.create_oval(2, 2, 18, 18, fill=checkbox_color, outline='')
                
                tool_text = f"{name}: {version}"
                tool_label = tk.Label(frame, text=tool_text, bg='#2d2d2d', 
                                    font=("Ubuntu", 9), fg='#ffffff', anchor='w', justify='left')
                tool_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                # Store tool info for selective export
                self.tool_checkboxes[name] = {
                    'frame': frame,
                    'name': name,
                    'version': version,
                    'status': status,
                    'category': category
                }

        # SYSTEM INFO AND EXPORT METHODS
    def show_system_info(self):
        try:
            system_info = f"""System Information:
• Ubuntu: {self.ubuntu_version}
• Architecture: {platform.machine()}
• Processor: {platform.processor()}
• Python: {platform.python_version()}
• Tkinter: {tk.TkVersion}

Hardware:
• CPU Cores: {os.cpu_count()}
• Total RAM: {self.get_total_ram()} GB
• Disk Space: {self.get_disk_space()}

License:
• Status: {self.get_trial_status()}
• Exports Used: {self.export_count}/{self.max_exports}
"""
            messagebox.showinfo("System Information", system_info)
        except Exception as e:
            messagebox.showerror("Error", f"Could not gather system info: {str(e)}")
    
    def get_total_ram(self):
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        mem_kb = int(line.split()[1])
                        return round(mem_kb / 1024 / 1024, 1)
        except:
            pass
        return "Unknown"
    
    def get_disk_space(self):
        try:
            total, used, free = shutil.disk_usage("/")
            return f"Total: {total // (2**30)}GB, Free: {free // (2**30)}GB"
        except:
            return "Unknown"
    
    def export_to_file(self):
        """Export results with trial limits"""
        if not self.check_trial_limits():
            return
            
        if not self.all_results:
            self.status_label.config(text="❌ No results to export!", fg='#ff4444')
            return
            
        try:
            default_filename = f"devscan_pro_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            filename = filedialog.asksaveasfilename(
                title="Export Tools Report",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=default_filename
            )
            
            if not filename:
                self.status_label.config(text="Export cancelled", fg='#ffff00')
                return
            
            # Increment export count for trial version
            if not self.activated:
                self.export_count += 1
                self.save_license_data()
            
            if filename.endswith('.json'):
                self.export_to_json(filename)
            else:
                self.export_to_txt(filename)
            
            status_msg = f"✅ Exported to: {os.path.basename(filename)}"
            if not self.activated:
                status_msg += f" ({self.max_exports - self.export_count} exports left)"
            
            self.status_label.config(text=status_msg, fg='#00ff00')
            
            # Open file manager
            subprocess.run(["xdg-open", os.path.dirname(filename)])
            
        except Exception as e:
            self.status_label.config(text=f"❌ Export failed: {str(e)}", fg='#ff4444')

    def export_to_txt(self, filename):
        with open(filename, 'w') as f:
            f.write(f"{self.app_name} - Development Tools Report\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"System: {self.ubuntu_version}\n")
            f.write(f"Architecture: {platform.machine()}\n")
            f.write(f"License: {self.get_trial_status()}\n")
            f.write("=" * 60 + "\n\n")
            
            categories = {}
            for name, version, status, category in self.all_results:
                if category not in categories:
                    categories[category] = []
                categories[category].append((name, version, status))
            
            for category, tools in categories.items():
                f.write(f"\n{category.upper()}:\n")
                f.write("-" * 40 + "\n")
                for name, version, status in tools:
                    status_icon = "✅" if status == "installed" else "❌"
                    f.write(f"{status_icon} {name}: {version}\n")
            
            installed_count = sum(1 for _, _, status, _ in self.all_results if status == "installed")
            f.write(f"\n\nSUMMARY:\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total tools checked: {len(self.all_results)}\n")
            f.write(f"Installed: {installed_count}\n")
            f.write(f"Missing: {len(self.all_results) - installed_count}\n")
            if self.all_results:
                f.write(f"Installation rate: {(installed_count/len(self.all_results))*100:.1f}%\n")
    
    def export_to_json(self, filename):
        report = {
            "app": self.app_name,
            "version": self.version,
            "vendor": self.vendor,
            "generated": datetime.datetime.now().isoformat(),
            "system": {
                "ubuntu": self.ubuntu_version,
                "architecture": platform.machine(),
                "python_version": platform.python_version()
            },
            "license": {
                "status": "activated" if self.activated else "trial",
                "trial_days_remaining": self.get_trial_days_remaining(),
                "exports_used": self.export_count,
                "max_exports": self.max_exports
            },
            "tools": [],
            "summary": {}
        }
        
        installed_count = 0
        for name, version, status, category in self.all_results:
            report["tools"].append({
                "name": name,
                "version": str(version),
                "status": status,
                "category": category
            })
            if status == "installed":
                installed_count += 1
        
        report["summary"] = {
            "total": len(self.all_results),
            "installed": installed_count,
            "missing": len(self.all_results) - installed_count,
            "installation_rate": round((installed_count/len(self.all_results))*100, 1) if self.all_results else 0
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
    
    def copy_to_clipboard(self):
        if not self.all_results:
            self.status_label.config(text="❌ No results to copy!", fg='#ff4444')
            return
            
        try:
            clipboard_text = f"{self.app_name} - Tools Report\n"
            clipboard_text += f"Checked: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            clipboard_text += f"System: {self.ubuntu_version}\n"
            clipboard_text += f"License: {self.get_trial_status()}\n\n"
            
            installed_count = 0
            for name, version, status, category in self.all_results:
                status_icon = "✅" if status == "installed" else "❌"
                clipboard_text += f"{status_icon} {name}: {version}\n"
                if status == "installed":
                    installed_count += 1
            
            clipboard_text += f"\nSummary: {installed_count}/{len(self.all_results)} tools installed"
            
            self.root.clipboard_clear()
            self.root.clipboard_append(clipboard_text)
            
            self.status_label.config(text="✅ Copied to clipboard!", fg='#00ff00')
            
        except Exception as e:
            self.status_label.config(text=f"❌ Copy failed: {str(e)}", fg='#ff4444')

        # SELECTIVE EXPORT METHODS
    def show_selective_export_dialog(self):
        """Show dialog for selecting tools to export"""
        if not self.all_results:
            messagebox.showwarning("No Data", "Please scan for tools first.")
            return
        
        # Create selection window
        select_window = tk.Toplevel(self.root)
        select_window.title("Select Tools for Export")
        select_window.geometry("600x500")
        select_window.configure(bg='#2b2b2b')
        
        # Main frame
        main_frame = ttk.Frame(select_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(main_frame, text="🎯 Select Tools to Export", 
                              font=("Ubuntu", 14, "bold"), 
                              bg='#2b2b2b', fg='#ffffff')
        title_label.pack(pady=(0, 10))
        
        # Instructions
        instr_label = tk.Label(main_frame, 
                              text="Select individual tools or use the buttons below to select all/none",
                              font=("Ubuntu", 10), 
                              bg='#2b2b2b', fg='#cccccc')
        instr_label.pack(pady=(0, 10))
        
        # Selection buttons frame
        selection_buttons_frame = tk.Frame(main_frame, bg='#2b2b2b')
        selection_buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        select_all_btn = tk.Button(selection_buttons_frame, text="Select All",
                                  command=lambda: self._toggle_all_checkboxes(select_window, True),
                                  bg='#4CAF50', fg='white',
                                  font=("Ubuntu", 9, "bold"))
        select_all_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        select_none_btn = tk.Button(selection_buttons_frame, text="Select None",
                                   command=lambda: self._toggle_all_checkboxes(select_window, False),
                                   bg='#f44336', fg='white',
                                   font=("Ubuntu", 9, "bold"))
        select_none_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        select_installed_btn = tk.Button(selection_buttons_frame, text="Select Installed Only",
                                       command=lambda: self._select_installed_only(select_window),
                                       bg='#2196F3', fg='white',
                                       font=("Ubuntu", 9, "bold"))
        select_installed_btn.pack(side=tk.LEFT)
        
        # Scrollable frame for checkboxes
        canvas = tk.Canvas(main_frame, bg='#1e1e1e', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Store checkboxes
        self.export_checkboxes = {}
        
        # Group tools by category
        categories = {}
        for name, version, status, category in self.all_results:
            if category not in categories:
                categories[category] = []
            categories[category].append((name, version, status))
        
        # Create checkboxes for each tool
        for category, tools in categories.items():
            # Category label
            cat_frame = tk.Frame(scrollable_frame, bg='#3a3a3a', relief='raised', bd=1)
            cat_frame.pack(fill=tk.X, pady=(5, 2), padx=5)
            cat_label = tk.Label(cat_frame, text=category, bg='#3a3a3a', 
                               font=("Ubuntu", 10, "bold"), fg='#ffffff', anchor='w')
            cat_label.pack(fill=tk.X, padx=10, pady=2)
            
            for name, version, status in tools:
                frame = tk.Frame(scrollable_frame, bg='#2d2d2d', relief='flat', bd=1)
                frame.pack(fill=tk.X, pady=1, padx=5)
                
                # Checkbox
                var = tk.BooleanVar(value=True)  # Default to selected
                checkbox = tk.Checkbutton(frame, variable=var, bg='#2d2d2d', 
                                        activebackground='#2d2d2d', selectcolor='#2d2d2d')
                checkbox.pack(side=tk.LEFT, padx=(10, 5))
                
                # Tool info
                status_icon = "✅" if status == "installed" else "❌"
                tool_text = f"{status_icon} {name}: {version}"
                tool_label = tk.Label(frame, text=tool_text, bg='#2d2d2d', 
                                    font=("Ubuntu", 9), fg='#ffffff', anchor='w')
                tool_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                self.export_checkboxes[name] = {
                    'var': var,
                    'name': name,
                    'version': version,
                    'status': status,
                    'category': category
                }
        
        # Export buttons frame
        export_buttons_frame = tk.Frame(main_frame, bg='#2b2b2b')
        export_buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        export_txt_btn = tk.Button(export_buttons_frame, text="Export as TXT",
                                  command=lambda: self._export_selected_tools(select_window, 'txt'),
                                  bg='#007acc', fg='white',
                                  font=("Ubuntu", 10, "bold"))
        export_txt_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        export_json_btn = tk.Button(export_buttons_frame, text="Export as JSON",
                                   command=lambda: self._export_selected_tools(select_window, 'json'),
                                   bg='#9c27b0', fg='white',
                                   font=("Ubuntu", 10, "bold"))
        export_json_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        cancel_btn = tk.Button(export_buttons_frame, text="Cancel",
                              command=select_window.destroy,
                              bg='#666', fg='white',
                              font=("Ubuntu", 10))
        cancel_btn.pack(side=tk.RIGHT)
    
    def _toggle_all_checkboxes(self, window, state):
        """Toggle all checkboxes to selected or unselected"""
        for tool_data in self.export_checkboxes.values():
            tool_data['var'].set(state)
    
    def _select_installed_only(self, window):
        """Select only installed tools"""
        for tool_data in self.export_checkboxes.values():
            tool_data['var'].set(tool_data['status'] == 'installed')
    
    def _export_selected_tools(self, window, export_format):
        """Export selected tools to file"""
        if not self.check_trial_limits():
            return
        
        # Get selected tools
        selected_tools = []
        for tool_data in self.export_checkboxes.values():
            if tool_data['var'].get():
                selected_tools.append((
                    tool_data['name'],
                    tool_data['version'],
                    tool_data['status'],
                    tool_data['category']
                ))
        
        if not selected_tools:
            messagebox.showwarning("No Selection", "Please select at least one tool to export.")
            return
        
        try:
            default_filename = f"devscan_pro_selected_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if export_format == 'json':
                filename = filedialog.asksaveasfilename(
                    title="Export Selected Tools",
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                    initialfile=default_filename + ".json"
                )
            else:
                filename = filedialog.asksaveasfilename(
                    title="Export Selected Tools",
                    defaultextension=".txt",
                    filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                    initialfile=default_filename + ".txt"
                )
            
            if not filename:
                return
            
            # Increment export count for trial version
            if not self.activated:
                self.export_count += 1
                self.save_license_data()
            
            if export_format == 'json':
                self._export_selected_to_json(filename, selected_tools)
            else:
                self._export_selected_to_txt(filename, selected_tools)
            
            status_msg = f"✅ Selected tools exported to: {os.path.basename(filename)}"
            if not self.activated:
                status_msg += f" ({self.max_exports - self.export_count} exports left)"
            
            self.status_label.config(text=status_msg, fg='#00ff00')
            window.destroy()
            
            # Open file manager
            subprocess.run(["xdg-open", os.path.dirname(filename)])
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
    
    def _export_selected_to_txt(self, filename, selected_tools):
        """Export selected tools to TXT file"""
        with open(filename, 'w') as f:
            f.write(f"{self.app_name} - Selected Tools Report\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"System: {self.ubuntu_version}\n")
            f.write(f"Tools Selected: {len(selected_tools)}\n")
            f.write("=" * 60 + "\n\n")
            
            categories = {}
            for name, version, status, category in selected_tools:
                if category not in categories:
                    categories[category] = []
                categories[category].append((name, version, status))
            
            for category, tools in categories.items():
                f.write(f"\n{category.upper()}:\n")
                f.write("-" * 40 + "\n")
                for name, version, status in tools:
                    status_icon = "✅" if status == "installed" else "❌"
                    f.write(f"{status_icon} {name}: {version}\n")
            
            installed_count = sum(1 for _, _, status, _ in selected_tools if status == "installed")
            f.write(f"\n\nSUMMARY:\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total tools selected: {len(selected_tools)}\n")
            f.write(f"Installed: {installed_count}\n")
            f.write(f"Missing: {len(selected_tools) - installed_count}\n")
            if selected_tools:
                f.write(f"Installation rate: {(installed_count/len(selected_tools))*100:.1f}%\n")
    
    def _export_selected_to_json(self, filename, selected_tools):
        """Export selected tools to JSON file"""
        report = {
            "app": self.app_name,
            "version": self.version,
            "vendor": self.vendor,
            "generated": datetime.datetime.now().isoformat(),
            "system": {
                "ubuntu": self.ubuntu_version,
                "architecture": platform.machine(),
                "python_version": platform.python_version()
            },
            "export_type": "selective",
            "tools_selected": len(selected_tools),
            "license": {
                "status": "activated" if self.activated else "trial",
                "trial_days_remaining": self.get_trial_days_remaining(),
                "exports_used": self.export_count,
                "max_exports": self.max_exports
            },
            "tools": [],
            "summary": {}
        }
        
        installed_count = 0
        for name, version, status, category in selected_tools:
            report["tools"].append({
                "name": name,
                "version": str(version),
                "status": status,
                "category": category
            })
            if status == "installed":
                installed_count += 1
        
        report["summary"] = {
            "total": len(selected_tools),
            "installed": installed_count,
            "missing": len(selected_tools) - installed_count,
            "installation_rate": round((installed_count/len(selected_tools))*100, 1) if selected_tools else 0
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

    # INSTALLATION SCRIPT METHODS
    def export_installation_script(self):
        """Export installation script for missing tools"""
        if not self.check_trial_limits():
            return
            
        if not self.all_results:
            self.status_label.config(text="❌ No results to export!", fg='#ff4444')
            return
        
        # Get missing tools
        missing_tools = []
        for name, version, status, category in self.all_results:
            if status == "not_installed" and name in self.tool_packages:
                missing_tools.append(name)
        
        if not missing_tools:
            messagebox.showinfo("No Missing Tools", 
                              "All detected tools are already installed!\n\n"
                              "There's nothing to generate an installation script for.")
            return
        
        try:
            default_filename = f"devscan_pro_install_script_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.sh"
            
            filename = filedialog.asksaveasfilename(
                title="Export Installation Script",
                defaultextension=".sh",
                filetypes=[("Shell scripts", "*.sh"), ("All files", "*.*")],
                initialfile=default_filename
            )
            
            if not filename:
                self.status_label.config(text="Export cancelled", fg='#ffff00')
                return
            
            # Increment export count for trial version
            if not self.activated:
                self.export_count += 1
                self.save_license_data()
            
            self._generate_installation_script(filename, missing_tools)
            
            status_msg = f"✅ Installation script exported: {os.path.basename(filename)}"
            if not self.activated:
                status_msg += f" ({self.max_exports - self.export_count} exports left)"
            
            self.status_label.config(text=status_msg, fg='#00ff00')
            
            # Show success dialog with instructions
            self._show_installation_instructions(filename, missing_tools)
            
        except Exception as e:
            self.status_label.config(text=f"❌ Export failed: {str(e)}", fg='#ff4444')

    def _generate_installation_script(self, filename, missing_tools):
        """Generate bash installation script"""
        with open(filename, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write(f"# DevScan Pro - Installation Script\n")
            f.write(f"# Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Tools to install: {len(missing_tools)}\n")
            f.write("#\n")
            f.write("# WARNING: This script will install software on your system.\n")
            f.write("# Review the commands below before running.\n")
            f.write("# Run with: bash " + os.path.basename(filename) + "\n")
            f.write("\n")
            f.write("set -e  # Exit on any error\n")
            f.write("\n")
            f.write('echo "🔧 DevScan Pro - Automated Tool Installation"\n')
            f.write('echo "==========================================="\n')
            f.write('echo ""\n')
            f.write("\n")
            
            # Group tools by package manager
            tools_by_manager = {}
            for tool_name in missing_tools:
                if tool_name in self.tool_packages:
                    package_info = self.tool_packages[tool_name]
                    manager = package_info["manager"]
                    package = package_info["package"]
                    
                    if manager not in tools_by_manager:
                        tools_by_manager[manager] = []
                    tools_by_manager[manager].append((tool_name, package))
            
            # Update package lists first
            f.write('# Update package lists\n')
            f.write('echo "Updating package lists..."\n')
            f.write('sudo apt update\n')
            f.write('echo ""\n')
            f.write("\n")
            
            # Install tools by package manager
            for manager, tools in tools_by_manager.items():
                if manager == "apt":
                    f.write(f'# Install APT packages\n')
                    f.write(f'echo "Installing APT packages..."\n')
                    packages = " ".join([pkg for _, pkg in tools])
                    f.write(f'sudo apt install -y {packages}\n')
                    f.write('echo ""\n')
                    f.write("\n")
                    
                elif manager == "snap":
                    f.write(f'# Install Snap packages\n')
                    f.write(f'echo "Installing Snap packages..."\n')
                    for tool_name, package in tools:
                        f.write(f'sudo snap install {package}\n')
                    f.write('echo ""\n')
                    f.write("\n")
                    
                elif manager in ["pip", "pip3"]:
                    f.write(f'# Install Python packages via {manager}\n')
                    f.write(f'echo "Installing Python packages..."\n')
                    for tool_name, package in tools:
                        f.write(f'{manager} install {package}\n')
                    f.write('echo ""\n')
                    f.write("\n")
            
            # Special cases and post-installation steps
            f.write('# Special installation steps\n')
            f.write('echo "Running special installation steps..."\n')
            f.write("\n")
            
            # Node.js special handling (often needs setup)
            if "Node.js" in missing_tools:
                f.write('# Install Node.js (alternative method if needed)\n')
                f.write('if ! command -v node &> /dev/null; then\n')
                f.write('    echo "Installing Node.js via NodeSource..."\n')
                f.write('    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -\n')
                f.write('    sudo apt-get install -y nodejs\n')
                f.write('fi\n')
                f.write("\n")
            
            # Docker special handling
            if "Docker" in missing_tools:
                f.write('# Install Docker (official method)\n')
                f.write('if ! command -v docker &> /dev/null; then\n')
                f.write('    echo "Installing Docker..."\n')
                f.write('    # Add Docker\'s official GPG key\n')
                f.write('    sudo apt-get install -y ca-certificates curl\n')
                f.write('    sudo install -m 0755 -d /etc/apt/keyrings\n')
                f.write('    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc\n')
                f.write('    sudo chmod a+r /etc/apt/keyrings/docker.asc\n')
                f.write('    \n')
                f.write('    # Add the repository to Apt sources\n')
                f.write('    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \\\n')
                f.write('    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null\n')
                f.write('    sudo apt-get update\n')
                f.write('    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin\n')
                f.write('fi\n')
                f.write("\n")
            
            f.write('echo ""\n')
            f.write('echo "✅ Installation completed!"\n')
            f.write('echo "Run \\\"devscan_pro.py\\\" to verify all installations."\n')
            
        # Make the script executable
        os.chmod(filename, 0o755)

    def _show_installation_instructions(self, filename, missing_tools):
        """Show instructions for using the installation script"""
        instructions = f"""📦 Installation Script Generated!

Script: {os.path.basename(filename)}
Tools to install: {len(missing_tools)}

To use this script:

1. Open terminal in the script directory
2. Make executable (if needed):
   chmod +x {os.path.basename(filename)}
3. Review the script:
   cat {os.path.basename(filename)}
4. Run the script:
   ./{os.path.basename(filename)}

OR run directly with:
   bash {os.path.basename(filename)}

Tools that will be installed:
{chr(10).join(['• ' + tool for tool in missing_tools])}

⚠️  Always review scripts before running them!"""

        messagebox.showinfo("Installation Script Generated", instructions)
        
        # Ask if user wants to open the script location
        if messagebox.askyesno("Open Location", "Do you want to open the script location in file manager?"):
            subprocess.run(["xdg-open", os.path.dirname(filename)])

def main():
    """Main entry point for package"""
    root = tk.Tk()
    app = DevScanPro(root)
    root.mainloop()

if __name__ == "__main__":
    main()
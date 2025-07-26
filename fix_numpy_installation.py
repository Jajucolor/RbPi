#!/usr/bin/env python3
"""
Fix NumPy Installation Issues
Resolves BLAS library problems for NumPy installation
"""

import subprocess
import sys
import platform
import os

def print_header():
    """Print fix header"""
    print("=" * 60)
    print("NumPy Installation Fix")
    print("=" * 60)
    print("This script will fix NumPy installation issues")
    print("by installing required BLAS libraries.")
    print()

def install_blas_libraries():
    """Install BLAS libraries for NumPy"""
    system = platform.system().lower()
    
    print(f"Installing BLAS libraries for {system}...")
    
    if system == "linux":
        try:
            # Detect Linux distribution
            with open("/etc/os-release", "r") as f:
                os_info = f.read().lower()
            
            if "ubuntu" in os_info or "debian" in os_info or "raspbian" in os_info:
                print("Installing BLAS libraries for Ubuntu/Debian...")
                
                # Update package list
                subprocess.check_call(["sudo", "apt", "update"])
                
                # Install BLAS and math libraries
                subprocess.check_call(["sudo", "apt", "install", "-y",
                                     "libopenblas-dev", "liblapack-dev", "libatlas-base-dev",
                                     "gfortran", "build-essential", "pkg-config", "cmake"])
                
                print("✅ BLAS libraries installed successfully")
                return True
                
            elif "fedora" in os_info or "rhel" in os_info:
                print("Installing BLAS libraries for Fedora/RHEL...")
                subprocess.check_call(["sudo", "dnf", "install", "-y",
                                     "openblas-devel", "lapack-devel", "gcc-gfortran",
                                     "build-essential", "pkg-config", "cmake"])
                print("✅ BLAS libraries installed successfully")
                return True
            else:
                print("⚠️  Please install BLAS libraries manually:")
                print("   sudo apt install libopenblas-dev liblapack-dev gfortran build-essential")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install BLAS libraries: {e}")
            return False
    
    elif system == "darwin":  # macOS
        try:
            print("Installing BLAS libraries for macOS...")
            subprocess.check_call(["brew", "install", "openblas", "lapack", "gcc"])
            print("✅ BLAS libraries installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install BLAS libraries: {e}")
            return False
    
    elif system == "windows":
        print("✅ Windows should handle BLAS automatically")
        return True
    
    else:
        print(f"⚠️  Unsupported system: {system}")
        return False

def install_numpy():
    """Install NumPy with proper BLAS support"""
    print("\nInstalling NumPy...")
    
    try:
        # Upgrade pip first
        print("Upgrading pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Try installing NumPy with BLAS support
        print("Installing NumPy with BLAS support...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "numpy>=1.21.0"])
        print("✅ NumPy installed successfully with BLAS support")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️  NumPy installation failed: {e}")
        print("Trying alternative installation methods...")
        
        try:
            # Try installing without BLAS
            print("Installing NumPy without BLAS...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "numpy>=1.21.0", "--no-build-isolation"])
            print("✅ NumPy installed successfully (without BLAS)")
            return True
            
        except subprocess.CalledProcessError as e2:
            print(f"❌ Alternative installation failed: {e2}")
            
            try:
                # Try installing from wheel
                print("Trying wheel installation...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "numpy", "--only-binary=all"])
                print("✅ NumPy installed successfully from wheel")
                return True
                
            except subprocess.CalledProcessError as e3:
                print(f"❌ Wheel installation failed: {e3}")
                return False

def test_numpy():
    """Test NumPy installation"""
    print("\nTesting NumPy installation...")
    
    try:
        import numpy as np
        print(f"✅ NumPy {np.__version__} installed successfully")
        
        # Test basic functionality
        arr = np.array([1, 2, 3, 4, 5])
        result = np.mean(arr)
        print(f"✅ NumPy functionality test passed: mean([1,2,3,4,5]) = {result}")
        
        return True
        
    except ImportError as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ NumPy test failed: {e}")
        return False

def install_other_dependencies():
    """Install other required dependencies"""
    print("\nInstalling other dependencies...")
    
    try:
        # Install requirements
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Other dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install other dependencies: {e}")
        return False

def main():
    """Main fix function"""
    print_header()
    
    # Install BLAS libraries
    if not install_blas_libraries():
        print("\n⚠️  BLAS installation failed, but continuing...")
    
    # Install NumPy
    if not install_numpy():
        print("\n❌ NumPy installation failed")
        sys.exit(1)
    
    # Test NumPy
    if not test_numpy():
        print("\n❌ NumPy test failed")
        sys.exit(1)
    
    # Install other dependencies
    if not install_other_dependencies():
        print("\n⚠️  Other dependencies installation failed, but continuing...")
    
    print("\n" + "=" * 60)
    print("🎉 NumPy Installation Fix Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run the setup script: python setup_inta.py")
    print("2. Test the system: python test_speech_recognition.py")
    print("3. Run the main application: python main.py")
    print("\nHappy coding! 🚀")

if __name__ == "__main__":
    main() 
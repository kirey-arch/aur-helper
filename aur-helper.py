import subprocess
import shutil
import os
from difflib import get_close_matches

def run(cmd):
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return result.stdout.decode()
    except subprocess.CalledProcessError as e:
        print(f"\n[!] ERROR WHILE EXECUTING: {cmd}")
        print(e.stdout.decode())
        return None

def is_installed(tool):
    return shutil.which(tool) is not None

def install_helper(helper):
    print(f"{helper} not found.")
    choice = input(f"Do you want to install {helper}? (y/n): ").lower()
    if choice == "y":
        if not is_installed("git"):
            print("Git not found. Installing git via pacman...")
            run("sudo pacman -Sy git --noconfirm")
        print(f"Cloning {helper} repository...")
        run(f"git clone https://aur.archlinux.org/{helper}.git")
        os.chdir(helper)
        run("makepkg -si --noconfirm")
        os.chdir("..")
        run(f"rm -rf {helper}")
    else:
        print("Alright, exiting...")
        exit()

def check_package_exists(source, pkg):
    print(f"Checking if '{pkg}' exists using {source}...")
    out = run(f"{source} -Ss ^{pkg}$")
    if out:
        lines = out.splitlines()
        for line in lines:
            if f"/{pkg} " in line:
                return True
    return False

def search_similar_interactive(source, name):
    print("Searching for similar packages...")
    out = run(f"{source} -Ss {name}")
    if not out:
        print("No results found.")
        return None

    lines = out.splitlines()
    package_names = []

    for line in lines:
        if "/" in line:
            try:
                package_name = line.split("/")[1].split()[0]
                package_names.append(package_name)
            except IndexError:
                continue

    package_names = list(dict.fromkeys(package_names))

    similar = get_close_matches(name, package_names, n=10, cutoff=0.3)

    if not similar:
        print("No similar packages found.")
        return None

    print("\n🔍 Similar packages found:")
    for i, s in enumerate(similar):
        print(f"{i + 1}. {s}")

    try:
        choice = int(input("\nEnter the number of the package you want to install/uninstall/purge (0 to cancel): "))
        if choice == 0:
            print("Cancelled.")
            return None
        elif 1 <= choice <= len(similar):
            return similar[choice - 1]
        else:
            print("Invalid option.")
            return None
    except ValueError:
        print("Invalid input.")
        return None

def install_package(source, pkg):
    print(f"Installing {pkg} with {source}...")
    output = run(f"{source} -S {pkg} --noconfirm")
    if output:
        print(output)
        print(f"✅ Package '{pkg}' installed successfully.")
    else:
        print(f"❌ Failed to install package '{pkg}'.")

def remove_package(source, pkg, mode="simple"):
    print(f"Removing {pkg} with {source}... (If an error occurs, check if the app was already removed. If so, ignore it.)")
    if mode == "simple":
        run(f"sudo {source} -Rns {pkg} --noconfirm")
    elif mode == "full":
        run(f"sudo {source} -Rns {pkg} --noconfirm")
        run("sudo pacman -Rns $(pacman -Qtdq) --noconfirm")
    elif mode == "purge":
        run(f"sudo {source} -Rns {pkg} --noconfirm")
        run("sudo pacman -Rns $(pacman -Qtdq) --noconfirm")
        run("sudo pacman -Sc --noconfirm")

def main_menu():
    print("\n--- MENU ---")
    print("1. Install package")
    print("2. Remove package (simple)")
    print("3. Remove package + unused dependencies")
    print("4. PURGE everything")
    return input("Choose an option: ")

def main():
    print("Choose your package manager:")
    print("1. Pacman")
    print("2. Yay")
    print("3. Paru")
    option = input("Enter the corresponding number: ")

    if option == "1":
        source = "pacman"
    elif option == "2":
        source = "yay"
    elif option == "3":
        source = "paru"
    else:
        print("Invalid option.")
        return
    
    if source != "pacman" and not is_installed(source):
        install_helper(source)

    action = main_menu()
    package = input("Enter the name of the package: ")

    if not check_package_exists(source, package):
        choice = search_similar_interactive(source, package)
        if choice:
            package = choice
        else:
            return

    if action == "1":
        install_package(source, package)
    elif action == "2":
        remove_package(source, package, "simple")
    elif action == "3":
        remove_package(source, package, "full")
    elif action == "4":
        remove_package(source, package, "purge")
    else:
        print("Invalid option.")

if __name__ == "__main__":
    main()
